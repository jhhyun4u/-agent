# Plan: 제안서작성 서비스 플랫폼 v1

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v1 |
| 작성일 | 2026-03-05 |
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

### 성공 기준
- 팀원 초대 후 제안서 공동 검토가 가능하다
- 과거 제안서 목록에서 수주/낙찰 이력을 조회할 수 있다
- 나라장터 실제 경쟁사 데이터가 Phase 1 분석에 반영된다
- 외부 고객사가 가입 후 독립적으로 제안서를 생성할 수 있다

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
- 제안서 생성 UI (RFP 업로드 → 진행상태 → 결과 다운로드)
- 팀 협업 (댓글/검토 상태 관리)
- 제안서 이력 DB (수주/낙찰 결과 저장)
- **나라장터 API 연동** (입찰공고 검색, 계약결과 조회, 업체이력 조회)

### v2 이후 (보류)
- 지식베이스 학습 (수주/낙찰 데이터 기반 LLM 프롬프트 자동 개선)
- 과금/구독 관리 (Stripe 연동, Free/Pro/Enterprise 플랜)
- 나라장터 API 키 사용자 관리 UI

---

## 4. v1 아키텍처

```
[Next.js 14] 프론트엔드
  ├─ /login              ← Supabase Auth
  ├─ /proposals          ← 제안서 목록 + 신규 생성
  ├─ /proposals/:id      ← 진행상태 실시간 + 결과 뷰어 + 댓글
  ├─ /team               ← 팀원 마이페이지
  └─ /admin              ← 팀 관리 (초대/권한)

[FastAPI] 백엔드
  ├─ /api/v3.1/*         ← 현재 유지 (5-Phase 파이프라인)
  ├─ /auth/*             ← 신규 (JWT 검증, 팀 권한)
  ├─ /api/team/*         ← 신규 (팀 CRUD, 댓글, 상태)
  └─ /api/g2b/*          ← 신규 (나라장터 API 프록시)

[Supabase]
  ├─ auth.users
  ├─ teams               (id, name, created_by)
  ├─ team_members        (team_id, user_id, role: admin/member/viewer)
  ├─ proposals           (id, title, status, owner_id, team_id, win_result)
  ├─ proposal_phases     (proposal_id, phase_num, artifact_json)
  ├─ comments            (proposal_id, section, user_id, body, created_at)
  └─ g2b_cache           (query_hash, result_json, cached_at)

[나라장터 Open API]
  ├─ getBidPblancListInfoServc    ← 입찰공고 검색
  ├─ getContractResultListInfo   ← 계약결과 조회
  └─ getCmpnyBidInfoServc        ← 업체 입찰이력 조회
```

---

## 5. 나라장터 API 연동 설계

### 현재 상태
`app/services/g2b_service.py`에 mock 데이터 기반 구현 완료.
실제 API 키만 있으면 `_mock_search_contracts` → 실제 API 호출로 교체 가능한 구조.

### 구현 작업
| 작업 | 파일 | 내용 |
|------|------|------|
| API 키 환경변수 추가 | .env | G2B_API_KEY |
| 실제 API 호출 구현 | g2b_service.py | _mock_ 함수 → aiohttp 실제 호출 |
| 응답 파싱 | g2b_service.py | XML/JSON 응답 → G2BContract 변환 |
| 결과 캐싱 | g2b_cache 테이블 | 동일 쿼리 24시간 캐시 |
| API 프록시 라우터 | /api/g2b/* | 프론트엔드에서 직접 호출 가능하도록 |

### 활용 흐름
```
RFP 업로드
  → Phase 1: G2B API로 유사 입찰공고 검색
  → 계약결과에서 낙찰업체 추출
  → 업체별 입찰이력으로 CompetitorProfile 생성
  → Phase 2 LLM에 실제 경쟁사 데이터 전달
  → 차별화 전략 + 가격 비딩 고도화
```

---

## 6. 작업 목록

### Phase A — 나라장터 실제 API 연동
| 순서 | 파일 | 작업 |
|------|------|------|
| A1 | .env / config.py | G2B_API_KEY 추가 |
| A2 | g2b_service.py | 실제 API 호출 구현 (3개 엔드포인트) |
| A3 | g2b_service.py | g2b_cache 테이블 캐싱 연동 |
| A4 | routes_v31.py | /api/g2b/search 프록시 엔드포인트 |

### Phase B — Supabase 세션 영속성 (GAP-2)
| 순서 | 파일 | 작업 |
|------|------|------|
| B1 | database/ | proposals, proposal_phases, teams, comments 테이블 생성 |
| B2 | session_manager.py | Supabase proposals 테이블 read/write 연동 |
| B3 | phase_executor.py | Phase 완료 시 proposal_phases에 artifact 저장 |

### Phase C — 프론트엔드 (Next.js)
| 순서 | 경로 | 작업 |
|------|------|------|
| C1 | /login | Supabase Auth UI |
| C2 | /proposals | 제안서 목록 + 생성 버튼 |
| C3 | /proposals/:id | SSE 진행상태 + 결과 뷰어 + 댓글 |
| C4 | /admin | 팀원 초대 + 권한 관리 |

### Phase D — 팀 협업 API
| 순서 | 파일 | 작업 |
|------|------|------|
| D1 | routes | /api/team/comments CRUD |
| D2 | routes | /api/team/proposals/:id/status (검토중/확정) |
| D3 | routes | /api/team/invite (이메일 초대) |

---

## 7. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| 나라장터 실제 경쟁사 데이터 반영 | Phase 1 결과에 실제 업체명 포함 |
| 팀원 초대 후 제안서 공동 접근 | 다른 계정으로 로그인 후 댓글 작성 |
| 서버 재시작 후 세션 유지 | /execute 후 서버 재시작 → /status 정상 응답 |
| 제안서 이력 DB 저장 | 과거 제안서 목록 조회 가능 |

---

## 8. 다음 단계

```
/pdca design proposal-platform-v1
```
