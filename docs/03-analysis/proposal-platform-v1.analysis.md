# Gap Analysis: proposal-platform-v1

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v1 |
| 분석일 | 2026-03-06 (설계 v10 최종 기준) |
| 기준 설계 | docs/02-design/features/proposal-platform-v1.design.md |
| 기준 코드 | v3.4 현재 codebase |
| **Match Rate** | **10%** |
| 상태 | 구현 미시작 (설계 v10 최종 확정 — 구현 시작 단계) |

---

## 요약

v3.4 codebase는 platform v1의 **시작 기반(baseline)** 이며, 설계된 플랫폼 기능 대부분이 아직 구현되지 않은 상태입니다.
설계가 v6 → v10으로 진화하면서 요구사항이 더욱 정밀해졌고, 구현 기준 Match Rate는 v6 대비 소폭 하향(12% → 10%)됩니다.

---

## 섹션별 Gap 분석

### 1. 아키텍처 기반 (30% → 가중 3점)

| 항목 | 설계 요구 | 현재 상태 | Gap |
|------|----------|----------|-----|
| FastAPI 백엔드 | uvicorn --workers 1, CORS settings.cors_origins | 서버 존재, allow_origins=["*"] | cors_origins 환경변수 연동 필요 |
| JWT 인증 미들웨어 | app/middleware/auth.py | 디렉토리 없음 | 신규 작성 |
| /api/team/* 라우터 | routes_team.py | 없음 | 신규 작성 |
| /api/g2b/* 라우터 | routes_g2b.py | 없음 | 신규 작성 |
| Supabase 연동 | acreate_client + asyncio.Lock + Storage + Realtime | 동기 SupabaseClient 클래스 (create_client) | 전체 재작성 |
| Next.js 프론트엔드 | frontend/ 전체 | 없음 | 신규 구축 |
| lifespan | mark_stale + cache cleanup + try/except | output/ 디렉토리 생성만 | Supabase RPC 호출 추가 |

---

### 2. DB 스키마 (0%)

설계에 정의된 8개 신규 테이블 모두 미구현.
현재 database/supabase_schema.sql은 구버전(proposals+personnel+reference_materials+documents) — 설계 요구와 완전히 다름.

| 테이블 | 현재 | Gap |
|--------|------|-----|
| teams | 없음 | DDL 작성 |
| team_members | 없음 | DDL 작성 |
| invitations | 없음 | DDL 작성 (ON CONFLICT upsert + invited_by ON DELETE SET NULL) |
| proposals (신규) | 다른 스키마 존재 | 전체 재작성 (owner_id ON DELETE RESTRICT 명시, rfp_content, current_phase 등) |
| proposal_phases | 없음 | DDL 작성 |
| comments | 없음 | DDL 작성 |
| usage_logs | 없음 | DDL 작성 (team_id/owner_id ON DELETE SET NULL) |
| g2b_cache | 없음 | DDL 작성 |
| RLS 정책 13개 | 구버전 8개 (auth.role 방식, 설계와 무관) | proposals + comments + phases + usage_logs + teams + team_members + invitations |
| 트리거/함수 | update_updated_at_column (이름 불일치) | update_updated_at + mark_stale + cleanup_expired_g2b_cache |
| pg_trgm 검색 인덱스 | GIN(to_tsvector) 존재 (다른 용도) | pg_trgm + gin_trgm_ops (ILIKE 부분일치용) |
| REPLICA IDENTITY FULL | 없음 | proposals 테이블 설정 + Dashboard Replication 활성화 |

---

### 3. 인증 미들웨어 (0%)

| 항목 | 설계 요구 | 현재 상태 | Gap |
|------|----------|----------|-----|
| acreate_client + asyncio.Lock | get_async_client() | 동기 SupabaseClient.create_client() | 전체 교체 |
| JWT 검증 (auth.get_user) | app/middleware/auth.py | 없음 | 신규 작성 |
| Depends(get_current_user) | 모든 보호 라우터 | 없음 | 각 엔드포인트 추가 |
| CORS settings.cors_origins | allow_origins=settings.cors_origins | allow_origins=["*"] | config.py + main.py 수정 |
| lifespan Supabase init | mark_stale + cache cleanup (try/except) | OS makedirs만 | lifespan 재작성 |

---

### 4. proposal_id 생성 (0%)

| 항목 | 설계 | 현재 | Gap |
|------|------|------|-----|
| UUID4 | str(uuid.uuid4()) | f"prop_{datetime.now()...}" (routes_v31.py:44) | 수정 |

---

### 5. API 엔드포인트 (20%)

기본 v3.1 엔드포인트 5개 + bid/calculate + templates 존재. 설계 요구사항 미반영.

| 엔드포인트 | 현재 | Gap |
|-----------|------|-----|
| POST /generate | 인증 없음, timestamp ID, 동기 session | JWT + UUID4 + owner_id + async session |
| POST /execute | start_phase 없음, BackgroundTasks | start_phase 파라미터 + asyncio.create_task |
| GET /download | local FileResponse | Storage 서명 URL + file_type 먼저 검증 |
| GET /invitations/accept | 없음 | ?team_id= 파라미터 + JWT email 조회 |
| /api/team/* (11개) | 없음 | 전체 신규 작성 |
| /api/g2b/* (5개) | 없음 | 전체 신규 작성 |

---

### 6. 나라장터 실제 API 연동 (0%)

| 항목 | 현재 | Gap |
|------|------|-----|
| 실제 aiohttp 호출 | _mock_search_contracts() | mock 제거 + _call_api 구현 |
| serviceKey URL 직접 포함 | 없음 (params dict 방식) | quote(key, safe="") + URL 문자열 포함 |
| G2B 응답 파싱 | 없음 | resultCode "00" 체크 + body.items.item 추출 |
| 낙찰결과 4단계 흐름 | 없음 | getBidResultListInfo 포함 4단계 구현 |
| Rate Limiting | 없음 | asyncio.sleep(0.1) + retry backoff |
| g2b_cache DB 연동 | 없음 | SHA256 해시 + 24h 캐싱 |

---

### 7. 세션 영속성 + async 전환 (5%)

| 항목 | 설계 | 현재 | Gap |
|------|------|------|-----|
| session_manager async | 모든 메서드 async | 전부 sync | 전체 변환 |
| Supabase DB 연동 | DB INSERT/SELECT/UPDATE | 인메모리 dict | 전체 재작성 |
| create_session DB first | DB INSERT 먼저 → 인메모리 | 인메모리만 | ghost session 방지 패턴 |
| phase_executor async | _update_status async | sync (현재 동기 호출) | async 전환 |
| _save_artifact upsert | proposal_phases 테이블 | 인메모리만 | 신규 구현 |
| _log_usage | usage_logs 테이블 | 없음 | 신규 구현 |
| _handle_failure | failed_phase + notes 기록 | 없음 | 신규 구현 |

---

### 8. 파일 저장소 (0%)

| 항목 | 현재 | Gap |
|------|------|-----|
| Storage 업로드 | 로컬 output/ 저장 | bucket 업로드 + content-type 지정 |
| Storage 서명 URL | local FileResponse | create_signed_url + RedirectResponse |
| _upload_to_storage finally 패턴 | 없음 | docx_ok/pptx_ok flag + finally 블록 (부분 실패 방지) |
| storage_upload_failed 처리 | 없음 | 플래그 기록 + 로컬 폴백 |
| docx_builder bytes 반환 | path만 반환 | (bytes, path) 튜플 수정 |
| pptx_builder bytes 반환 | path만 반환 | (bytes, path) 튜플 수정 |

---

### 9. 실시간 상태 + 알림 (0%)

| 항목 | 현재 | Gap |
|------|------|-----|
| Realtime DB 쓰기 | 없음 (인메모리) | session_manager DB 연동 선행 필요 |
| REPLICA IDENTITY FULL | 없음 | Dashboard Replication 설정 필요 |
| proposal-complete Edge Function | 없음 | status guard + admin.getUserById + Resend |
| comment-notify Edge Function | 없음 | event.record + {data: proposal} 구조분해 + proposal?.team_id |
| Database Webhooks 설정 | 없음 | Dashboard > Database > Webhooks |
| team_id NULL 케이스 | 해당 없음 | proposal?.team_id 옵셔널 체이닝 처리 |

---

### 10. 프론트엔드 (0%)

frontend/ 디렉토리 자체가 없음. Next.js 14 앱 전체 신규 구축 필요.

| 항목 | Gap |
|------|-----|
| Next.js 프로젝트 초기화 | npx create-next-app@14 |
| middleware.ts | @supabase/ssr + cookies handler + getUser() |
| @supabase/ssr 설정 | createServerClient + createBrowserClient |
| 6개 페이지 | login, onboarding, proposals, [id], admin, invitations/accept |
| 8개 컴포넌트 | PhaseProgress, ResultViewer, FileUploadZone, PhaseRetryButton 등 |
| Realtime 훅 | usePhaseStatus, useProposals |
| lib/api.ts | 401 감지 → signOut + /login 리다이렉트 |

---

## 매치율 산정 근거

| 섹션 | 배점 | 점수 | 근거 |
|------|------|------|------|
| 아키텍처 기반 | 10 | 3 | FastAPI + CORS 존재 (allow_origins 미흡) |
| DB 스키마 | 15 | 0 | 전혀 없음 (구버전 스키마 별도 존재) |
| 인증 미들웨어 | 10 | 0 | 없음 |
| proposal_id UUID4 | 5 | 0 | 타임스탬프 사용 중 |
| API 엔드포인트 | 15 | 3 | 기본 v3.1 엔드포인트만 (인증/팀/G2B 없음) |
| G2B 실제 연동 | 10 | 0 | mock만 존재 (serviceKey/파싱 패턴 없음) |
| 세션 영속성 + async | 10 | 1 | phase_executor 부분 async만 |
| 파일 저장소 | 10 | 0 | 없음 |
| 실시간 + 알림 | 10 | 0 | 없음 |
| 프론트엔드 | 15 | 0 | 없음 |
| **합계** | **100** | **7 → 보정 10%** | 설계 v10 요구사항 강화로 v6 대비 소폭 하향 |

---

## 구현 우선순위 (Do 단계 로드맵)

```
[Step 1 - DB + 기반 인프라]
  database/schema.sql              8개 테이블 + 13개 RLS + pg_trgm + REPLICA IDENTITY
  app/utils/supabase_client.py     acreate_client + asyncio.Lock (동기 클래스 폐기)
  app/config.py                    g2b_api_key, cors_origins 추가, .hwp 제거
  app/main.py                      CORSMiddleware(settings.cors_origins) + lifespan try/except
  app/middleware/auth.py           JWT 검증 — Optional[str] Header(None)

[Step 2 - 세션 영속성 + 파이프라인]
  app/services/session_manager.py  전체 async + DB INSERT 먼저 + DB 복원
  app/services/phase_executor.py   async + _save_artifact + _log_usage + _handle_failure
  app/api/routes_v31.py            UUID4, await, start_phase, Storage URL

[Step 3 - 파일 저장소]
  app/services/docx_builder.py     (bytes, path) 튜플 반환
  app/services/pptx_builder.py     (bytes, path) 튜플 반환
  app/services/phase_executor.py   _upload_to_storage (finally 패턴 + content-type)

[Step 4 - G2B 실제 API]
  app/services/g2b_service.py      _call_api (serviceKey URL + 응답 파싱) + 4단계 + retry
  app/api/routes_g2b.py            G2B 프록시 라우터

[Step 5 - 팀 협업 API]
  app/api/routes_team.py           역할 기반 권한 + 초대 + 페이지네이션 + 검색
  supabase/functions/              proposal-complete + comment-notify
  Dashboard                        Webhooks + Secrets + Replication 설정

[Step 6 - 프론트엔드]
  Next.js 초기화 + @supabase/ssr
  middleware.ts (cookies handler + getUser)
  페이지 + 컴포넌트 구현
  Realtime 훅 + 세션 만료 처리
```

---

## 다음 단계

Match Rate 10% → 설계 v10 최종 확정. 구현을 시작합니다.

**첫 번째 작업: Step 1-A — `database/schema.sql` 작성**

```
Step 1-A: database/schema.sql
  - 8개 테이블 DDL (proposals.owner_id ON DELETE RESTRICT 명시)
  - 13개 RLS 정책
  - pg_trgm + gin_trgm_ops 인덱스
  - REPLICA IDENTITY FULL
  - mark_stale_running_proposals / cleanup_expired_g2b_cache 함수

Step 1-B: app/utils/supabase_client.py
  - acreate_client + asyncio.Lock 싱글턴 (동기 클래스 폐기)

Step 1-C: app/config.py
  - g2b_api_key, cors_origins 필드 추가 / .hwp 제거

Step 1-D: app/main.py
  - CORSMiddleware(settings.cors_origins)
  - lifespan: mark_stale + cache cleanup (try/except)

Step 1-E: app/middleware/auth.py
  - get_current_user — Optional[str] Header(None)
```

설계 v10 주요 확정 사항:
- proposals.owner_id ON DELETE RESTRICT (명시적 기재, 계정 삭제 전 proposals 이관 필요)
- Storage 업로드: content-type 지정 + finally 패턴으로 부분 실패 처리
- G2B: serviceKey URL 직접 포함 + resultCode 체크 + body.items 파싱
- comment-notify: {data: proposal} 구조분해 + proposal?.team_id 옵셔널 체이닝
- proposal-complete: status !== "completed" guard
- create_session: DB INSERT 먼저 (ghost session 방지)
- ILIKE 검색: pg_trgm + gin_trgm_ops (text_pattern_ops 교체)
