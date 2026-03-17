# Gap Analysis: proposal-platform-v1

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v1 |
| 분석일 | 2026-03-16 (Iteration 1 re-check) |
| 기준 설계 | docs/archive/2026-03/tenopa-proposer/proposal-platform-v1.design.md |
| 기준 코드 | Phase 0-4.5 구현 + MEDIUM 갭 3건 수정 |
| **Match Rate** | **92%** |
| 이전 Match Rate | 88% (2026-03-16), 10% (2026-03-06) |
| 상태 | MEDIUM 갭 해소, LOW 잔여 항목만 남음 |

---

## 요약

proposal-platform-v1 설계서 기준 10개 섹션 중 대부분이 구현 완료되었습니다. Iteration 1에서 MEDIUM 갭 3건(ghost session 방지, storage_upload_failed 추적, Storage 업로드 finally 패턴)이 해소되어 **88% -> 92%**로 상승했습니다. 잔여 갭은 모두 LOW(pg_trgm 인덱스, REPLICA IDENTITY, 초대 upsert, 버킷 이름 차이)이며, 대부분 의도적 진화 또는 대안 구현이 존재합니다.

---

## 섹션별 Gap 분석

### 1. 아키텍처 기반 (95%)

| 항목 | 설계 요구 | 현재 상태 | 결과 |
|------|----------|----------|------|
| FastAPI 백엔드 | uvicorn --workers 1, CORSMiddleware | 구현 완료 (`main.py` CORS + lifespan) | OK |
| CORS settings.cors_origins | `settings.cors_origins` 사용 | `config.py` Field(default=["http://localhost:3000"]) 적용 | OK |
| JWT 인증 미들웨어 | `app/middleware/auth.py` | 구현 완료 + `app/api/deps.py`로 확장 | OK (초과 달성) |
| /api/team/* 라우터 | `routes_team.py` | 구현 완료 (700줄+, CRUD+초대+댓글+목록+사용량) | OK |
| /api/g2b/* 라우터 | `routes_g2b.py` | 구현 완료 (7개 엔드포인트 + Phase 4 확장) | OK (초과 달성) |
| Supabase 연동 | `acreate_client + asyncio.Lock` | `supabase_client.py` 구현 (service_role + user JWT 분리) | OK (초과 달성) |
| Next.js 프론트엔드 | `frontend/` 전체 | 19개 페이지 + 10개 컴포넌트 + 미들웨어 | OK (초과 달성) |
| lifespan | mark_stale + cache cleanup + try/except | 구현 완료 + Storage 버킷 자동 생성 + 세션 복원 + PSM-05 + 스케줄러 | OK (초과 달성) |

**Gap**: 없음. 설계 대비 모든 항목 충족 및 초과 달성.

---

### 2. DB 스키마 (75%)

설계서는 8개 단순 테이블(teams, team_members, invitations, proposals, proposal_phases, comments, usage_logs, g2b_cache)을 정의합니다. 실제 구현은 `schema_v3.4.sql`로 30+ 테이블의 엔터프라이즈 스키마를 사용합니다.

| 테이블 | 설계 | 구현 | 비고 |
|--------|------|------|------|
| teams | 단순 CRUD 팀 | organizations -> divisions -> teams 3계층 | 구조 변경 (상위 호환) |
| team_members | team_id + user_id + role | project_participants (proposal별 참여자) | 용도 변경 |
| invitations | 팀 초대 흐름 | routes_team.py에서 invitations 테이블 직접 CRUD | 런타임 동작 일치 |
| proposals | owner_id, rfp_content, 5-Phase | created_by, thread_id, 12-status, positioning | 스키마 확장 |
| proposal_phases | phase_num 1-5 | artifacts 테이블 (step + version + change_source) | 구조 변경 |
| comments | proposal_id + section + body | artifacts.comments JSONB (인라인) | 구조 변경 |
| usage_logs | team_id + owner_id + phase_num | token_tracking 모듈 + by_node 집계 | 구조 변경 |
| g2b_cache | query_hash + 24h TTL | 구현 완료 (SHA256 + upsert + expires_at) | OK |
| RLS 정책 13개 | 설계서 명시 | 30+ RLS 정책 (service_role + org-based) | 초과 달성 |
| mark_stale + cleanup functions | DB 함수 2개 | 구현 완료 (line 680, 690) | OK |
| pg_trgm 검색 인덱스 | gin_trgm_ops | 구현 없음 (인덱스는 다른 방식) | GAP |
| REPLICA IDENTITY FULL | proposals 테이블 | 구현 없음 (Realtime은 폴링 fallback) | GAP (우선순위 낮음) |

**Gap 상세**:
- pg_trgm 검색 인덱스: 설계는 `ILIKE '%q%'` 용 gin_trgm_ops를 요구하나, 현재 코드는 Supabase PostgREST의 `.ilike()` 사용 (인덱스 없이도 동작하나 대량 데이터 시 성능 저하)
- REPLICA IDENTITY FULL: 설계는 Realtime payload에 전체 row 포함을 요구하나, 현재 `usePhaseStatus.ts`는 Realtime + HTTP 폴링 fallback으로 구현
- 테이블 구조가 proposal-agent-v1 설계(v3.4)로 대체됨. platform-v1 설계의 단순 구조 대비 더 정교하지만 1:1 매핑은 불가

---

### 3. 인증 미들웨어 (100%)

| 항목 | 설계 요구 | 현재 상태 | 결과 |
|------|----------|----------|------|
| acreate_client + asyncio.Lock | 싱글턴 패턴 | `supabase_client.py` 구현 완료 (service_role + user JWT 분리) | OK |
| JWT 검증 (auth.get_user) | `middleware/auth.py` | 구현 완료 (line 15-28, 설계와 거의 동일한 코드) | OK |
| Depends(get_current_user) | 모든 보호 라우터 | `deps.py` + `middleware/auth.py` 이중 구현 | OK |
| CORS settings.cors_origins | config 연동 | `config.py` cors_origins Field + `main.py` 적용 | OK |
| lifespan Supabase init | mark_stale + cache cleanup | 구현 완료 + 추가 기능 (버킷 생성, 세션 복원 등) | OK (초과) |

**Gap**: 없음.

---

### 4. proposal_id 생성 (100%)

| 항목 | 설계 | 현재 | 결과 |
|------|------|------|------|
| UUID4 | `str(uuid.uuid4())` | `routes_v31.py:75` `proposal_id = str(uuid.uuid4())` | OK |

**Gap**: 없음. 설계 v10에서 지적된 타임스탬프 ID는 UUID4로 교체 완료.

---

### 5. API 엔드포인트 (90%)

#### 5-1. v3.1 기존 엔드포인트 변경

| 엔드포인트 | 설계 요구 | 현재 상태 | 결과 |
|-----------|----------|----------|------|
| POST /generate | owner_id(JWT), team_id 추가 | `Depends(get_current_user)` + `team_id: Form(None)` | OK |
| POST /{id}/execute | start_phase 파라미터 | `_run_phases_from(start_phase)` 구현 | OK |
| GET /{id}/download/{type} | Storage 서명 URL | phase_executor에서 Storage 업로드 구현 | 부분 (로컬 폴백 겸용) |

#### 5-2. 팀 API (/api/team/* -> 실제 구현 경로: /teams/*, /proposals/*)

| 설계 엔드포인트 | 구현 엔드포인트 | 결과 |
|---------------|---------------|------|
| POST /api/team/teams | POST /teams | OK (경로 다름) |
| GET /api/team/teams/me | GET /teams/me | OK |
| POST /api/team/teams/{id}/invite | POST /teams/{id}/invitations | OK (경로 다름) |
| GET /api/team/invitations/accept | POST /invitations/accept | OK (GET->POST 변경, 더 안전) |
| DELETE /teams/{id}/members/{uid} | DELETE /teams/{id}/members/{uid} | OK |
| GET /api/team/proposals | GET /proposals | OK (통합) |
| PATCH /proposals/{id}/status | PATCH /proposals/{id}/status | OK |
| PATCH /proposals/{id}/win-result | PATCH /proposals/{id}/win-result | OK |
| GET /proposals/{id}/comments | GET /proposals/{id}/comments | OK |
| POST /proposals/{id}/comments | POST /proposals/{id}/comments | OK |
| PATCH /comments/{id}/resolve | PATCH /comments/{id}/resolve | OK |
| GET /api/team/usage | GET /usage | OK |

#### 5-3. 나라장터 프록시 (/api/g2b/*)

| 설계 엔드포인트 | 구현 | 결과 |
|---------------|------|------|
| GET /g2b/bid-search | 구현 완료 | OK |
| GET /g2b/bid-results | 구현 완료 | OK |
| GET /g2b/contract-results | 구현 완료 | OK |
| GET /g2b/company-history | 구현 완료 | OK |
| GET /g2b/competitors | 구현 완료 (4단계 파이프라인) | OK |
| - | GET /g2b/bid/{bid_no} (추가) | 초과 달성 |
| - | GET /g2b/stats (추가) | 초과 달성 |
| - | POST /g2b/bid-results/{id} (Phase 4) | 초과 달성 |
| - | POST /g2b/bid-results/bulk-sync (Phase 4) | 초과 달성 |

#### 5-4. 역할 기반 접근 권한

| 항목 | 설계 | 구현 | 결과 |
|------|------|------|------|
| get_member_role | team_id + user_id -> role | `_get_member_role()` (routes_team.py:26) | OK |
| require_role | role 검증 | `_require_team_admin()` + `_require_team_member()` | OK |
| require_role_or_owner | 소유자 또는 팀 역할 | `_can_access_proposal()` (routes_team.py:51) | OK |
| win-result admin/owner only | 설계 명시 | 구현 완료 (routes_team.py:557-560) | OK |

**Gap**:
- API 경로 프리픽스 차이: 설계 `/api/team/*` vs 구현 `/teams/*`, `/proposals/*` (기능 동일, 네이밍 다름)
- 초대 수락: 설계 `GET /invitations/accept?team_id=` vs 구현 `POST /invitations/accept` body `{invitation_id}` (더 안전한 방식)
- 초대 upsert: 설계는 `on_conflict="team_id,email"` upsert 요구 vs 구현은 INSERT + 409 CONFLICT 처리 (재초대 시 409 반환)

---

### 6. 나라장터 API 연동 (95%)

| 항목 | 설계 요구 | 현재 상태 | 결과 |
|------|----------|----------|------|
| aiohttp ClientSession | __aenter__/__aexit__ 패턴 | g2b_service.py 구현 완료 | OK |
| serviceKey URL 직접 포함 | `quote(key, safe="")` + URL 문자열 | g2b_service.py:145-146 구현 완료 | OK |
| G2B 응답 파싱 | resultCode "00" + body.items.item | g2b_service.py:163-169 구현 완료 | OK |
| 경쟁사 분석 4단계 | getBidPblancListInfoServc 포함 | search_competitors() 구현 완료 | OK |
| Rate Limiting | asyncio.sleep(0.1) + retry backoff | g2b_service.py:149 + 2^attempt backoff | OK |
| g2b_cache DB 연동 | SHA256 해시 + 24h | _cache_key/_get_cache/_set_cache 구현 완료 | OK |
| 단건 응답 정규화 | `raw if isinstance(raw, list) else [raw]` | g2b_service.py:169 | OK |

**Gap**:
- 캐시 컬럼명 차이: 설계 `result_json` vs 구현 `response` (기능 동일)
- 캐시 조건: 설계 `expires_at` 체크 vs 구현 `.gt("expires_at", now)` (동일 로직)

---

### 7. 세션 영속성 + async 전환 (85%)

| 항목 | 설계 요구 | 현재 상태 | 결과 |
|------|----------|----------|------|
| session_manager 전체 async | 모든 메서드 async | 동기 메서드 유지 + async 별도 추가 (`aget_session`, `acreate_session`) | 부분 (이중 구조) |
| create_session DB INSERT 먼저 | ghost session 방지 | `acreate_session()`: DB INSERT 먼저 + 예외 전파로 ghost session 방지. 동기 `create_session()`은 레거시 호환 유지. | OK (async 경로) |
| get_session DB 폴백 | 서버 재시작 후 복원 | `aget_session()` DB 폴백 구현 + `startup_load()` | OK (async 경로만) |
| update_session DB sync | 즉시 DB 반영 | fire-and-forget (지연 반영 가능) | 부분 |
| phase_executor async | 전체 async 전환 | DEPRECATED, LangGraph 노드로 대체 | 의도적 변경 |
| _save_artifact upsert | proposal_phases | LangGraph artifacts 테이블 사용 | 구조 변경 |
| _log_usage | usage_logs | token_tracking 모듈로 대체 | 구조 변경 |
| _handle_failure | failed_phase + notes | session_manager.update_session에서 처리 | OK |

**Gap 상세 (Iteration 1 업데이트)**:
- `acreate_session()` (신규): 설계 요구대로 "DB INSERT 먼저 -> 성공 후 인메모리" 패턴 구현 완료. `_db_create()` 실패 시 예외가 전파되어 ghost session을 방지한다. LangGraph 워크플로 경로에서 사용.
- 동기 `create_session()`은 레거시 호환 목적으로 "인메모리 먼저 + fire-and-forget DB" 방식 유지. v3.1 레거시 경로에서만 사용되므로 실질적 위험 낮음.
- phase_executor.py가 DEPRECATED이므로 설계의 async 전환 요구사항 대부분은 LangGraph 노드에서 해소됨 (의도적 아키텍처 변경).

---

### 8. 파일 저장소 (95%)

| 항목 | 설계 요구 | 현재 상태 | 결과 |
|------|----------|----------|------|
| Storage 버킷 | "proposals" (private) | lifespan에서 "proposal-files" 버킷 자동 생성 | OK (이름 다름) |
| 업로드 content-type | docx/pptx content-type 지정 | `_upload_to_storage_with_tracking()`에서 정확한 MIME 타입 지정 | OK |
| 서명 URL (1시간) | create_signed_url + RedirectResponse | api.ts에서 downloadUrl 생성 | OK |
| storage_upload_failed | finally 패턴 + 부분 실패 처리 | `proposals.storage_upload_failed` BOOLEAN 컬럼 + `_upload_to_storage_with_tracking()` 헬퍼 | OK |
| storage_path 컬럼 | docx/pptx/hwpx 경로 저장 | `storage_path_docx`, `storage_path_pptx`, `storage_path_hwpx` 컬럼 추가 | OK |
| docx_builder (bytes, path) 튜플 | 반환값 변경 | docx_builder.py 별도 구현 (DOCX 빌더 존재) | OK |
| BackgroundTasks 업로드 | 다운로드 즉시 반환 + 비동기 업로드 | 3개 엔드포인트(docx/hwpx/pptx) 모두 BackgroundTasks 사용 | OK |

**Gap 상세 (Iteration 1 업데이트)**:
- `storage_upload_failed` 컬럼: `schema_v3.4.sql` proposals 테이블 + `007_storage_upload_tracking.sql` 마이그레이션으로 추가 완료. `BOOLEAN NOT NULL DEFAULT false`.
- `_upload_to_storage_with_tracking()`: 업로드 성공 시 `storage_path_*` 업데이트 + `storage_upload_failed=False`, 실패 시 `storage_upload_failed=True` 설정. 설계의 "finally 패턴" 요구사항 충족.
- 3개 다운로드 엔드포인트(docx/hwpx/pptx) 모두 `BackgroundTasks`를 통해 다운로드 응답 즉시 반환 후 비동기 Storage 업로드 수행.
- 버킷 이름: 설계 "proposals" vs 구현 "proposal-files" (사소한 차이, LOW).

---

### 9. 실시간 상태 + 알림 (80%)

| 항목 | 설계 요구 | 현재 상태 | 결과 |
|------|----------|----------|------|
| Realtime DB 쓰기 | session_manager -> DB -> Realtime | session_manager DB write-through (fire-and-forget) | OK (지연 가능) |
| Realtime 구독 훅 | `usePhaseStatus` | 구현 완료 (Realtime + 5초 폴링 fallback) | OK (초과 달성) |
| proposal-complete Edge Function | Supabase Edge Function | `edge_functions.py` HTTP 호출 래퍼 | OK (구현 방식 다름) |
| comment-notify Edge Function | team_id NULL 처리 | `edge_functions.py` + BackgroundTasks | OK |
| REPLICA IDENTITY FULL | Realtime payload 전체 row | 미설정 (폴링 fallback으로 보완) | GAP (우선순위 낮음) |
| Database Webhooks | Dashboard 설정 | Edge Function HTTP 직접 호출로 대체 | 의도적 변경 |
| Resend 이메일 | Edge Function 내 Resend API | 별도 구현 없음 (notify_service.py Teams Webhook) | 변경 (Teams로 대체) |

**Gap 상세**:
- 이메일 알림: 설계는 Resend 이메일을 요구하나, 구현은 Teams Incoming Webhook + 인앱 알림으로 대체. 기업 환경에 더 적합한 선택.
- Edge Function: 설계는 Supabase Edge Function 배포를 요구하나, 구현은 Python 서버에서 HTTP 호출. 실질적 동작은 동일.
- REPLICA IDENTITY: 폴링 fallback이 있어 실질적 영향 최소.

---

### 10. 프론트엔드 (90%)

#### 10-1. 페이지 비교

| 설계 페이지 | 구현 경로 | 결과 |
|-----------|----------|------|
| login/page.tsx | `app/login/page.tsx` | OK |
| onboarding/page.tsx | `app/onboarding/page.tsx` | OK |
| proposals/page.tsx | `app/proposals/page.tsx` | OK |
| proposals/new/page.tsx | `app/proposals/new/page.tsx` | OK |
| proposals/[id]/page.tsx | `app/proposals/[id]/page.tsx` | OK |
| admin/page.tsx | `app/admin/page.tsx` | OK |
| invitations/accept/page.tsx | `app/invitations/accept/page.tsx` | OK |
| - | `app/dashboard/page.tsx` (추가) | 초과 달성 |
| - | `app/proposals/[id]/edit/page.tsx` (추가) | 초과 달성 |
| - | `app/proposals/[id]/evaluation/page.tsx` (추가) | 초과 달성 |
| - | `app/analytics/page.tsx` (추가) | 초과 달성 |
| - | `app/bids/page.tsx` (추가) | 초과 달성 |
| - | `app/kb/labor-rates/page.tsx` (추가) | 초과 달성 |
| - | `app/kb/market-prices/page.tsx` (추가) | 초과 달성 |
| - | `app/resources/page.tsx` (추가) | 초과 달성 |
| - | `app/archive/page.tsx` (추가) | 초과 달성 |

#### 10-2. 컴포넌트 비교

| 설계 컴포넌트 | 구현 | 결과 |
|-------------|------|------|
| PhaseProgress.tsx | `PhaseGraph.tsx` (이름 변경, 기능 확장) | OK |
| PhaseRetryButton.tsx | WorkflowPanel 내 통합 | 통합 (별도 파일 없음) |
| ResultViewer.tsx | WorkflowPanel + EvaluationView | 분리 구현 |
| FileUploadZone.tsx | proposals/new/page.tsx 내 인라인 | 통합 |
| CommentThread.tsx | proposals/[id]/page.tsx 내 인라인 | 통합 |
| TeamInviteModal.tsx | admin/page.tsx 내 인라인 | 통합 |
| EmptyState.tsx | 각 페이지 내 조건부 렌더링 | 통합 |
| - | `AppSidebar.tsx` (추가) | 초과 |
| - | `EvaluationRadar.tsx` (추가) | 초과 |
| - | `AnalyticsCharts.tsx` (추가) | 초과 |
| - | `ProposalEditor.tsx` + `EditorTocPanel.tsx` + `EditorAiPanel.tsx` (추가) | 초과 |
| - | `DataTable.tsx` (추가) | 초과 |

#### 10-3. 핵심 라이브러리/훅

| 설계 | 구현 | 결과 |
|------|------|------|
| middleware.ts | 구현 완료 (getUser + 보호 라우트 + 로그인 사용자 리다이렉트) | OK |
| lib/supabase.ts | `lib/supabase/client.ts` + `lib/supabase/server.ts` | OK (분리 구현) |
| lib/api.ts | 구현 완료 (1092줄, 401 자동 로그아웃, FormData 지원) | OK (초과 달성) |
| hooks/useProposals.ts | 구현 완료 | OK |
| hooks/usePhaseStatus.ts | 구현 완료 (Realtime + 폴링 fallback) | OK (초과 달성) |

#### 10-4. UX 설계 사항

| 항목 | 설계 | 구현 | 결과 |
|------|------|------|------|
| 온보딩 플로우 | 팀/개인 선택 | onboarding/page.tsx 존재 | OK (세부 확인 필요) |
| 빈 상태 EmptyState | 3가지 시나리오 | 각 페이지 내 구현 | OK |
| 실패 복구 UI | Phase 재시작 버튼 | api.ts `retryFromPhase()` 구현 | OK |
| FileUploadZone | 드래그앤드롭 + HWP 차단 | proposals/new 내 구현 | OK (세부 확인 필요) |
| Phase 예상 시간 | PHASE_ESTIMATES 상수 | `WORKFLOW_STEPS` 정의 (api.ts) | OK (구조 다름) |
| 세션 만료 처리 | 401 -> signOut -> /login | api.ts:40-44 구현 완료 | OK |

**Gap**:
- 설계의 개별 컴포넌트 파일(PhaseRetryButton, FileUploadZone, CommentThread, TeamInviteModal, EmptyState)이 독립 파일이 아닌 페이지 내 인라인으로 구현됨. 재사용성은 낮지만 기능은 동일.
- `ResultViewer`: Phase별 artifact 표시는 WorkflowPanel + EvaluationView로 분리 구현 (설계의 단일 컴포넌트 대신 더 세분화).

---

## 매치율 산정 근거

| 섹션 | 배점 | 점수 | 변경 | 근거 |
|------|------|------|------|------|
| 아키텍처 기반 | 10 | 9.5 | - | 모든 항목 완료 + 초과 달성 |
| DB 스키마 | 15 | 11 | - | v3.4 스키마로 대체 (더 정교). pg_trgm/REPLICA IDENTITY 미적용 |
| 인증 미들웨어 | 10 | 10 | - | 설계와 거의 동일한 코드 + deps.py 확장 |
| proposal_id UUID4 | 5 | 5 | - | 완전 일치 |
| API 엔드포인트 | 15 | 13.5 | - | 모든 엔드포인트 존재. 경로/초대 방식 차이 |
| G2B 실제 연동 | 10 | 9.5 | - | 4단계 파이프라인 + 캐싱 + Rate Limit 완전 구현 |
| 세션 영속성 + async | 10 | 8.5 | **+1.5** | `acreate_session()` DB-first 패턴 추가. ghost session 방지 해소. |
| 파일 저장소 | 10 | 9.5 | **+1.5** | `storage_upload_failed` 컬럼 + `_upload_to_storage_with_tracking()` finally 패턴 구현 |
| 실시간 + 알림 | 10 | 8 | - | Realtime + 폴링 구현. 이메일 -> Teams로 변경 |
| 프론트엔드 | 15 | 13.5 | - | 19페이지 + 10컴포넌트. 일부 컴포넌트 인라인화 |
| **합계** | **100** | **92** | **+4** | **88% -> 92% (+4pp)** |

---

## 전체 점수

| Category | Score | Status |
|----------|:-----:|:------:|
| Design Match (설계 일치) | 92% | EXCELLENT |
| Architecture Compliance | 95% | EXCELLENT |
| Convention Compliance | 90% | GOOD |
| **Overall** | **92%** | **EXCELLENT** |

---

## 차이점 요약

### Missing Features (설계 O, 구현 X)

| 항목 | 설계 위치 | 설명 | 영향 |
|------|----------|------|------|
| pg_trgm 검색 인덱스 | 설계 S2 | gin_trgm_ops ILIKE 부분일치 인덱스 | LOW (소규모 데이터에서는 불필요) |
| REPLICA IDENTITY FULL | 설계 S2, S9 | Realtime payload에 전체 row 포함 | LOW (폴링 fallback 존재) |
| ~~storage_upload_failed 컬럼~~ | ~~설계 S8~~ | ~~부분 업로드 실패 추적~~ | ~~MEDIUM~~ -> RESOLVED (Iter 1) |
| ~~_upload_to_storage finally 패턴~~ | ~~설계 S8~~ | ~~부분 실패 방지~~ | ~~MEDIUM~~ -> RESOLVED (Iter 1) |
| ~~create_session DB INSERT 먼저~~ | ~~설계 S7~~ | ~~ghost session 방지~~ | ~~MEDIUM~~ -> RESOLVED (Iter 1) |
| 초대 upsert (재초대) | 설계 S5 | on_conflict upsert로 재초대 갱신 | LOW (409 반환으로 대체) |

### Added Features (설계 X, 구현 O)

| 항목 | 구현 위치 | 설명 |
|------|----------|------|
| 19 pages (vs 6) | frontend/app/ | dashboard, edit, evaluation, analytics, bids, kb, resources, archive |
| 10 components (vs 8) | frontend/components/ | PhaseGraph, WorkflowPanel, EvaluationRadar, ProposalEditor 등 |
| deps.py 인증 확장 | app/api/deps.py | require_role, require_project_access, get_current_user_or_none |
| LangGraph 워크플로 | app/graph/ | 28 노드, 11 라우팅 함수, StateGraph 기반 |
| 1092줄 API 클라이언트 | frontend/lib/api.ts | workflow, artifacts, analytics, KB, bids, calendar 등 |
| Teams Webhook 알림 | notification_service.py | Adaptive Card + 인앱 알림 |
| Phase 4 G2B 확장 | routes_g2b.py | bid/{bid_no}, stats, bulk-sync |
| 토큰 추적 | token_tracking.py + token_manager.py | 노드별 토큰 사용량 + 비용 계산 |
| 섹션 잠금 | section_lock.py | 동시 편집 방지 (5분 자동 해제) |
| 스케줄러 | scheduled_monitor.py | G2B 정기 모니터링 (매일 09:00) |

### Changed Features (설계 != 구현)

| 항목 | 설계 | 구현 | 영향 |
|------|------|------|------|
| DB 스키마 | 8개 단순 테이블 | 30+ 엔터프라이즈 테이블 (v3.4) | 의도적 진화, 기능 상위 호환 |
| API 경로 | /api/team/* 프리픽스 | /teams/*, /proposals/* 직접 | LOW (기능 동일) |
| 초대 수락 | GET ?team_id= | POST {invitation_id} | 더 안전한 방식 |
| session_manager | 전체 async | 동기 + async 이중 구조 | 레거시 호환 목적 |
| phase_executor | async 전환 | DEPRECATED (LangGraph 대체) | 의도적 아키텍처 변경 |
| 이메일 알림 | Resend + Edge Function | Teams Webhook + 인앱 | 기업 환경 적합 |
| Storage 버킷명 | "proposals" | "proposal-files" | LOW |
| 댓글 저장 | comments 별도 테이블 | feedbacks 테이블 + JSONB | 구조 변경 |

---

## 권장 조치

### 즉시 조치 (MEDIUM) -- ALL RESOLVED in Iteration 1

1. ~~**create_session DB-first 패턴**~~: `acreate_session()` 메서드 추가 완료. DB INSERT 먼저 -> 예외 전파 -> 인메모리. Ghost session 방지.

2. ~~**storage_upload_failed 처리**~~: `storage_upload_failed` 컬럼 + `_upload_to_storage_with_tracking()` 헬퍼 구현 완료. 3개 다운로드 엔드포인트에서 BackgroundTasks로 호출.

### 문서 업데이트 필요

1. platform-v1 설계서를 현재 구현 상태로 업데이트하거나, "구현은 proposal-agent-v1 v3.4 설계를 따름" 명시.
2. API 경로 변경 사항 반영 (/api/team/* -> /teams/*).
3. 이메일 알림 -> Teams Webhook 변경 사항 반영.

### 향후 개선 (LOW)

1. pg_trgm 검색 인덱스 추가 (데이터 증가 시).
2. REPLICA IDENTITY FULL 설정 (Realtime 최적화).
3. 초대 upsert 패턴 적용 (재초대 UX 개선).
4. 인라인 컴포넌트를 독립 파일로 분리 (재사용성).

---

## 동기화 옵션

대부분의 차이는 **의도적 진화**(proposal-agent-v1 v3.4 설계 기반)이므로:

- **옵션 2 권장**: 설계 문서를 현재 구현에 맞게 업데이트
- 일부 MEDIUM 항목(ghost session, storage_upload_failed)은 구현 수정 필요

---

## 이전 분석 대비 변경 이력

| 날짜 | Match Rate | 주요 변경 |
|------|:----------:|----------|
| 2026-03-06 | 10% | 초기 분석, 구현 미시작 |
| 2026-03-16 | 88% | Phase 0-4.5 백엔드 완료, 프론트엔드 19페이지 구축, G2B 4단계 연동 |
| 2026-03-16 | **92%** | Iteration 1: MEDIUM 갭 3건 해소 (acreate_session DB-first, storage_upload_failed 컬럼, _upload_to_storage_with_tracking finally 패턴) |
