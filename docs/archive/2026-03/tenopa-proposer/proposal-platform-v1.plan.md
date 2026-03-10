# Plan: 제안서작성 서비스 플랫폼 v1

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v1 |
| 작성일 | 2026-03-05 |
| 최종 수정 | 2026-03-06 (proposals 컬럼, F10, 다음 단계 업데이트) |
| 기반 | tenopa proposer v3.4 (현재 FastAPI 백엔드) |
| 목표 | 내부 도구 → SaaS 플랫폼 전환 |
| 우선순위 | High |

---

## 1. 사용자 의도 발견 (Plan Plus Phase 1)

### 핵심 문제
1. **사내 도구 → SaaS 전환**: 현재 내부 API만 있어 외부 고객이 직접 사용 불가
2. **팀 협업 부재**: 1인 API 호출 구조 — 여러 담당자가 함께 제안서를 검토/수정할 수 없음
3. **지식 축적 부재**: 수주/낙찰 결과가 저장되지 않아 다음 제안에 활용 불가

### 대상 사용자
- **제안 담당자 (PM/영업)**: RFP를 받아 제안서를 직접 작성하는 실무자
- **경영진/검토자**: 제안서를 최종 검토·승인하는 역할
- **외부 고객사**: SaaS 구독 후 직접 제안서를 생성하는 타 기업 담당자

### 성공 기준 (최종)
- 팀원 초대 후 제안서 공동 검토 및 댓글 작성이 가능하다
- 과거 제안서 목록에서 수주/낙찰 이력을 조회할 수 있다
- 나라장터 실제 경쟁사 데이터(낙찰업체명 포함)가 Phase 2 분석에 반영된다
- 외부 고객사가 가입 후 독립적으로 제안서를 생성할 수 있다
- Phase 실패 시 해당 Phase부터 재시작할 수 있다
- 제안서 생성 완료 시 이메일로 알림을 받는다
- 서버 재시작 후에도 세션이 복원된다

---

## 2. 탐색된 대안 (Plan Plus Phase 2)

### 선택: Approach A — 단일 앱 확장
현재 FastAPI 백엔드를 유지하면서 Next.js 프론트엔드 추가.
가장 빠른 시작, 현재 코드 재활용 최대화.

### 검토된 대안들
| 방식 | 장점 | 단점 | 결론 |
|------|------|------|------|
| A. 단일 앱 확장 | 빠른 시작, 코드 재활용 | 멀티테넌트 추후 리팩토링 필요 | **선택** |
| B. 멀티테넌트 SaaS | 조직 완전 격리, 과금 체계 명확 | 구축 복잡도 높음, Stripe 필요 | v2 |
| C. API-first | 유연성 최고, UI 불필요 | 고객 사용성 낮음 | 미채택 |

---

## 3. YAGNI 검토 (Plan Plus Phase 3)

### v1 포함 (필수)
- 로그인 / 팀 관리 (Supabase Auth)
- 온보딩 플로우 (신규 가입자 팀/개인 선택)
- 제안서 생성 UI (RFP 업로드 → 진행상태 실시간 → 결과 뷰어 → 다운로드)
- 팀 협업 (댓글/검토 상태 관리 + 댓글 알림 이메일)
- 제안서 이력 DB (수주/낙찰 결과 저장)
- **나라장터 API 연동** (입찰공고 검색, 낙찰결과 조회, 계약결과 조회, 업체이력 조회 — 4개)
- 파일 저장소 (Supabase Storage — 로컬 저장 대체)
- 완료 알림 이메일 (5~15분 대기 작업 특성상 필수)
- Phase 실패 복구 UI (재시작 버튼)
- 세션 영속성 (서버 재시작 후 DB 복원)
- 토큰 사용량 로깅 (비용 추적)

### v2 이후 (보류)
- 수주 통계 대시보드 (데이터 축적 선행 필요, 시각화는 v2에서 의미)
- 지식베이스 학습 (수주/낙찰 데이터 기반 LLM 프롬프트 자동 개선)
- 과금/구독 관리 (Stripe 연동, Free/Pro/Enterprise 플랜)
- 나라장터 API 키 사용자 관리 UI
- HWP 파일 지원 (라이브러리 불안정 — PDF/DOCX 변환 후 업로드 안내로 대체)

---

## 4. v1 아키텍처

```
[Next.js 14] 프론트엔드
  ├─ /login                  ← Supabase Auth
  ├─ /onboarding             ← 신규 가입자 팀/개인 선택
  ├─ /proposals              ← 제안서 목록 (검색, 필터, 페이지네이션)
  ├─ /proposals/new          ← RFP 업로드 (드래그앤드롭, PDF/DOCX/TXT)
  ├─ /proposals/:id          ← 진행상태 실시간 + 결과 뷰어 + 댓글
  ├─ /invitations/accept     ← 팀 초대 수락 콜백
  └─ /admin                  ← 팀 관리 (초대/권한)

[FastAPI] 백엔드  (uvicorn --workers 1 고정)
  ├─ /api/v3.1/*             ← 5-Phase 파이프라인 (JWT 인증 추가)
  ├─ /api/team/*             ← 팀 CRUD, 댓글, 초대, 상태
  └─ /api/g2b/*              ← 나라장터 API 프록시 + 24h 캐시

[Supabase]
  ├─ auth.users
  ├─ teams               (id, name, created_by)
  ├─ team_members        (team_id, user_id, role: admin/member/viewer)
  ├─ invitations         (team_id, email, role, status, expires_at)
  ├─ proposals           (id UUID4, title, status, owner_id, team_id,
  │                       current_phase, phases_completed, failed_phase,
  │                       rfp_filename, rfp_content, rfp_content_truncated,
  │                       storage_path_docx, storage_path_pptx, storage_path_rfp,
  │                       storage_upload_failed, win_result, bid_amount, notes)
  ├─ proposal_phases     (proposal_id, phase_num, artifact_json)
  ├─ comments            (proposal_id, section, user_id, body, resolved)
  ├─ usage_logs          (proposal_id, phase_num, model, input_tokens, output_tokens)
  └─ g2b_cache           (query_hash, result_json, expires_at)

[Supabase Storage]
  └─ bucket: proposals/  ← DOCX, PPTX, 원본 RFP (서명 URL 1시간)

[Supabase Edge Functions]
  ├─ proposal-complete   ← Phase5 완료 시 이메일 발송 (Resend)
  └─ comment-notify      ← 댓글 작성 시 팀원 이메일 발송

[나라장터 Open API]
  ├─ getBidPblancListInfoServc    ← 입찰공고 검색
  ├─ getBidResultListInfo         ← 낙찰결과 조회 (낙찰업체명 확보 필수)
  ├─ getContractResultListInfo    ← 계약결과 조회
  └─ getCmpnyBidInfoServc         ← 업체 입찰이력 조회
```

---

## 5. 나라장터 API 연동 설계

### 현재 상태
`app/services/g2b_service.py`에 mock 데이터 기반 구현 완료.
실제 API 키만 있으면 `_mock_search_contracts` -> 실제 API 호출로 교체 가능한 구조.

### 구현 작업
| 작업 | 파일 | 내용 |
|------|------|------|
| API 키 환경변수 추가 | .env | G2B_API_KEY |
| 실제 API 호출 구현 | g2b_service.py | _mock_ 함수 -> aiohttp 실제 호출 (_type=json) |
| 낙찰결과 조회 추가 | g2b_service.py | getBidResultListInfo (낙찰업체명 필수 확보) |
| 응답 파싱 | g2b_service.py | JSON 응답 -> G2BContract 변환 |
| 결과 캐싱 | g2b_cache 테이블 | 동일 쿼리 24시간 캐시 |
| API 프록시 라우터 | /api/g2b/* | 프론트엔드에서 직접 호출 가능하도록 |

### 활용 흐름 (4단계)
```
RFP 업로드
  -> Phase 1: G2B API 입찰공고 검색
  -> 낙찰결과 조회로 낙찰업체명 + 낙찰금액 확보
  -> 업체별 입찰이력으로 CompetitorProfile 생성
  -> Phase 2 LLM에 실제 경쟁사 데이터 전달
  -> 차별화 전략 + 가격 비딩 고도화
```

---

## 6. 핵심 기술 결정사항

| 결정 | 내용 | 이유 |
|------|------|------|
| 작업 실행 | uvicorn --workers 1 고정 | FastAPI BackgroundTasks는 인프로세스, 재시작 시 소실 |
| 세션 복원 | DB 기반 (proposals 테이블) | 재시작 후 running -> failed 마킹 + UI 재시작 버튼 |
| JWT 검증 | Supabase SDK auth.get_user() | JWKS 방식, PyJWT 직접 디코딩 불가 |
| Supabase 클라이언트 | AsyncClient (비동기) | FastAPI async 환경 필수 |
| proposal_id | uuid.uuid4() | 타임스탬프 기반 ID는 동시 생성 시 충돌 위험 |
| 파일 저장 | Supabase Storage (private bucket) | 로컬 output/ 디렉터리는 서버 재시작 시 접근 불가 |
| 실시간 상태 | Supabase Realtime (WebSocket) | SSE 대비 재연결 안정성, Supabase 기본 제공 |
| HWP 지원 | 제거 | hwplib 라이브러리 불안정, PDF/DOCX 변환 안내로 대체 |
| 완료 알림 | 이메일 v1 포함 (Resend 무료) | 5~15분 대기 작업, 브라우저 알림만으로는 사용성 부족 |

---

## 7. 작업 목록

### Phase A — DB + 기반 인프라
| 순서 | 파일 | 작업 |
|------|------|------|
| A1 | database/schema.sql | 전체 DDL 작성 (8개 테이블 + RLS + 트리거 + startup 함수) |
| A2 | app/config.py | G2B_API_KEY, CORS_ORIGINS 환경변수 추가, .hwp 제거 |
| A3 | app/utils/supabase_client.py | AsyncClient get_async_client() 구현 |
| A4 | app/main.py | CORSMiddleware + lifespan startup (stale 마킹, 캐시 정리) |
| A5 | app/middleware/auth.py | Supabase SDK JWT 검증 미들웨어 |

### Phase B — 세션 영속성 + 핵심 파이프라인 수정
| 순서 | 파일 | 작업 |
|------|------|------|
| B1 | app/services/session_manager.py | 전체 async 전환 + Supabase DB read/write 연동 |
| B2 | app/services/phase_executor.py | async 전환 (21곳) + _save_artifact upsert + _log_usage + _handle_failure |
| B3 | app/api/routes_v31.py | UUID4 적용, await 추가, start_phase 파라미터, JWT 인증 |

### Phase C — 파일 저장소 + 다운로드
| 순서 | 파일 | 작업 |
|------|------|------|
| C1 | app/services/phase_executor.py | Phase5 완료 후 Supabase Storage 업로드 |
| C2 | app/api/routes_v31.py /download | FileResponse -> Storage 서명 URL 리다이렉트 |
| C3 | app/services/docx_builder.py | 반환값에 bytes 추가 (Storage 업로드용) |
| C4 | app/services/pptx_builder.py | 반환값에 bytes 추가 |

### Phase D — 나라장터 실제 API 연동
| 순서 | 파일 | 작업 |
|------|------|------|
| D1 | app/services/g2b_service.py | mock 제거 + 실제 aiohttp 호출 + 낙찰결과 조회 추가 |
| D2 | app/services/g2b_service.py | g2b_cache 테이블 캐싱 연동 |
| D3 | app/api/routes_g2b.py | G2B 프록시 라우터 (신규) |
| D4 | app/api/routes.py | G2B 라우터 등록 |

### Phase E — 팀 협업 API + 알림
| 순서 | 파일 | 작업 |
|------|------|------|
| E1 | app/api/routes_team.py | 팀/초대/댓글/수주결과 + 페이지네이션 + 검색 (신규) |
| E2 | app/api/routes_team.py | 초대 수락 콜백 (/invitations/accept) |
| E3 | app/api/routes.py | 팀 라우터 등록 |
| E4 | supabase/functions/proposal-complete/ | 완료 이메일 Edge Function (Resend) |
| E5 | supabase/functions/comment-notify/ | 댓글 알림 Edge Function (team_id NULL 처리) |
| E6 | Supabase Dashboard | Edge Function Secrets 설정 (RESEND_API_KEY) |

### Phase F — 프론트엔드 (Next.js)
| 순서 | 경로/파일 | 작업 |
|------|----------|------|
| F1 | app/login + Supabase Auth | 로그인 + 토큰 자동 갱신 |
| F2 | app/onboarding | 신규 가입자 온보딩 (팀/개인 선택) |
| F3 | app/proposals | 목록 (검색 ?q=, 필터, 페이지네이션, EmptyState) |
| F4 | app/proposals/new | FileUploadZone (드래그앤드롭, 형식/크기 즉시 검증) |
| F5 | app/proposals/[id] | PhaseProgress (예상 시간) + ResultViewer + PhaseRetryButton |
| F6 | app/proposals/[id] | CommentThread + 댓글 작성 |
| F7 | app/invitations/accept | 초대 수락 콜백 처리 |
| F8 | app/admin | 팀원 초대 + 권한 관리 |
| F9 | lib/api.ts | 401 감지 -> 세션 만료 처리 + /login 리다이렉트 |
| F10 | frontend/middleware.ts | Next.js 인증 보호 라우트 (@supabase/ssr 기반) |

---

## 8. 성공 기준 (최종)

| 기준 | 검증 방법 |
|------|----------|
| 나라장터 실제 경쟁사 데이터 | Phase 2 결과에 실제 업체명 + 낙찰금액 포함 |
| 팀원 초대 후 공동 접근 | 다른 계정으로 로그인 후 댓글 작성 성공 |
| 서버 재시작 후 세션 유지 | /execute 후 서버 재시작 -> /status 200 복원 |
| 제안서 이력 DB 저장 | 과거 제안서 목록 조회 가능 |
| Phase 실패 복구 | 실패 후 재시작 버튼 클릭 -> 해당 Phase부터 재실행 |
| 완료 이메일 알림 | Phase5 완료 후 owner 이메일 수신 |
| 댓글 알림 이메일 | 댓글 작성 후 팀원 이메일 수신 |
| 파일 영속성 | 서버 재시작 후 /download 서명 URL 정상 |
| 온보딩 플로우 | 신규 가입 -> /onboarding -> 팀 생성 -> /proposals |
| 빈 상태 표시 | 제안서 0개 상태에서 EmptyState + 가이드 버튼 |
| 제안서 검색 | /proposals?q=키워드 제목 필터 동작 |
| HWP 업로드 차단 | .hwp 선택 시 즉시 오류 메시지 (서버 요청 전) |
| JWT 인증 | Bearer 없는 요청 -> 401 |
| CORS | Next.js localhost:3000 -> FastAPI 정상 통신 |
| 세션 만료 처리 | 만료 후 API 호출 -> /login 리다이렉트 |

---

## 9. 다음 단계

```
/pdca analyze proposal-platform-v1
```
