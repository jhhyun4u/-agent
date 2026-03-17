# API 엔드포인트 설계

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [01-architecture.md](01-architecture.md), [13-auth-notifications.md](13-auth-notifications.md)
> **원본 섹션**: §12

---

## 12. API 엔드포인트 설계

### 12-0. ★ 표준 에러 코드 체계 (v3.4)

> **배경**: ProposalForge의 구조화된 에러 코드 체계(`AUTH_001`, `PROJ_001` 등)를 참고하여 도입.
> ProposalEditor 자동저장(3초 debounce)이 빈번한 API 호출을 유발하므로,
> 에러 종류별 프론트엔드 핸들링(재시도/토큰갱신/인라인에러)을 명확히 구분하는 것이 핵심 목적.

#### 에러 응답 표준 형식

```json
{
  "error_code": "SECT_001",
  "message": "섹션이 다른 사용자에 의해 잠겨 있습니다.",
  "detail": {
    "locked_by": "홍길동",
    "locked_at": "2026-03-10T14:30:00Z",
    "expires_at": "2026-03-10T15:00:00Z"
  }
}
```

#### 에러 코드 프리픽스

| 프리픽스 | 도메인 | 예시 |
|----------|--------|------|
| `AUTH_` | 인증·인가 | 토큰 만료, 권한 부족 |
| `PROP_` | 프로젝트·워크플로 | 상태 전이 오류, 중복 생성 |
| `WF_` | 워크플로 실행 | resume 실패, 노드 오류 |
| `SECT_` | 섹션·편집 | 잠금 충돌, 버전 충돌 |
| `KB_` | Knowledge Base | 검색 오류, 임포트 실패 |
| `AI_` | AI 서비스 | Claude API 오류, 토큰 초과 |
| `FILE_` | 파일 처리 | 업로드 실패, 포맷 오류 |
| `ADMIN_` | 관리자 기능 | 조직 구조 오류, 템플릿 오류 |

#### 주요 에러 코드 테이블

| 에러 코드 | HTTP | 설명 | 프론트엔드 핸들링 |
|-----------|------|------|-------------------|
| `AUTH_001` | 401 | JWT 토큰 만료 | 자동 토큰 갱신 후 재시도 |
| `AUTH_002` | 403 | 역할 권한 부족 | 에러 토스트 + 접근 차단 |
| `AUTH_003` | 403 | 프로젝트 접근 권한 없음 | 에러 페이지 리다이렉트 |
| `PROP_001` | 409 | 프로젝트 상태 전이 불가 | 상태 새로고침 안내 |
| `PROP_002` | 404 | 프로젝트 없음 | 404 페이지 |
| `WF_001` | 409 | 워크플로 이미 실행 중 | 현재 상태 안내 |
| `WF_002` | 422 | resume 페이로드 검증 실패 | 인라인 폼 에러 |
| `SECT_001` | 423 | 섹션 잠금 충돌 | 잠금 소유자·만료 시간 표시 |
| `SECT_002` | 409 | 섹션 버전 충돌 (동시 편집) | 최신 버전 로드 안내 |
| `KB_001` | 422 | KB 임포트 데이터 검증 실패 | 오류 행 번호 표시 |
| `AI_001` | 503 | Claude API 일시 오류 | 자동 재시도 (3회, 지수 백오프) |
| `AI_002` | 422 | AI 요청 토큰 예산 초과 | 입력 축소 안내 |
| `AI_003` | 504 | AI 응답 타임아웃 | 재시도 버튼 표시 |
| `FILE_001` | 413 | 파일 크기 초과 (50MB) | 파일 크기 제한 안내 |
| `FILE_002` | 415 | 지원하지 않는 파일 형식 | 허용 형식 목록 안내 |

> **구현 패턴**: `app/api/deps.py`에 `TenopAPIError(Exception)` 기반 클래스 정의.
> FastAPI exception handler에서 표준 형식으로 직렬화. 기존 `HTTPException`을 점진적으로 교체.
> §22-4 Fallback 전략의 에러 분류(Claude API retry, external data skip, quality gate limits, timeouts)와 일관성 유지.

---

### 12-1. 워크플로 제어

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals` | 프로젝트 생성 (mode, search_query 포함) |
| POST | `/api/proposals/from-rfp` | RFP 업로드로 프로젝트 생성 (STEP 0 건너뛰고 STEP 1 직접 진입) |
| POST | `/api/proposals/from-search` | ★ 워크플로 밖에서 공고번호로 직접 프로젝트 생성 (rfp_fetch부터 시작) |
| GET  | `/api/proposals` | 프로젝트 목록 (포지셔닝·단계·마감일 포함, U-10) |
| GET  | `/api/proposals/{id}` | 프로젝트 상세 |
| POST | `/api/proposals/{id}/start` | 워크플로 시작 |
| GET  | `/api/proposals/{id}/state` | 현재 그래프 상태 |
| POST | `/api/proposals/{id}/resume` | Human 리뷰 결과 입력 → 그래프 재개 |
| POST | `/api/proposals/{id}/goto/{step}` | Time-travel |
| GET  | `/api/proposals/{id}/impact/{step}` | ★ 이전 단계 이동 시 영향 범위 조회 (U-5) |
| GET  | `/api/proposals/{id}/history` | 체크포인트 이력 |
| GET  | `/api/proposals/{id}/stream` | SSE 스트리밍 |
| POST | `/api/proposals/{id}/reopen` | ★ No-Go → Go 재전환 (D-9) |

### 12-1-1. 프로젝트 생성 API 요청 바디 (U-9)

```json
// POST /api/proposals — STEP 0(공고 검색)부터 시작
{
  "name": "AI 플랫폼 관련",
  "mode": "full",
  "search_query": {
    "keywords": "AI 플랫폼",
    "budget_min": 100000000,
    "region": "서울"
  }
}

// POST /api/proposals/from-rfp — STEP 0 건너뛰고 STEP 1 직접 시작
{
  "mode": "lite",
  "rfp_file": "<UploadFile>"
}

// POST /api/proposals/from-search — 워크플로 밖에서 공고번호 직접 지정 (rfp_fetch부터)
// ★ STEP 0(검색)을 건너뛰고, 이미 알고 있는 공고번호로 rfp_fetch → STEP 1 진입
{
  "bid_no": "20260309-001",
  "mode": "full"
}
```

> **3가지 진입 경로 정리**:
> | 경로 | API | 시작 노드 | 시나리오 |
> |------|-----|-----------|----------|
> | 공고 검색 | `POST /api/proposals` | `rfp_search` | 일반: 공고 탐색부터 시작 |
> | 공고번호 직접 | `POST /api/proposals/from-search` | `rfp_fetch` | 이미 공고를 알고 있음 |
> | RFP 업로드 | `POST /api/proposals/from-rfp` | `rfp_analyze` | RFP 문서를 가지고 있음 |

### 12-2. resume API 요청 바디

```json
// 빠른 승인 (U-2)
{
  "quick_approve": true,
  "approved_by": "홍길동"
}

// STEP 0: 공고 Pick-up
{
  "picked_bid_no": "20260309-001"
}

// STEP 0: 관심과제 없음 (워크플로 종료)
{
  "no_interest": true,
  "reason": "적합한 공고 없음. 예산 규모 및 기한이 맞지 않음."
}

// STEP 0: 재검색 (검색 조건 변경)
{
  "search_query": { "keywords": "AI 플랫폼", "budget_min": 100000000, "region": "서울" }
}

// STEP 0→1: RFP 파일 업로드 (rfp_fetch 게이트)
{
  "rfp_file_text": "... 파싱된 RFP 텍스트 ..."
}

// STEP 0→1: RFP 파일 없이 진행 (G2B 자동 추출분으로 진행)
{
  "skip_upload": true
}

// STEP 1-②: Go → 포지셔닝 확정
{
  "decision": "go",
  "positioning_override": "offensive",
  "approved_by": "김팀장"
}

// STEP 1-②: No-Go (프로젝트 종료)
{
  "decision": "no_go",
  "no_go_reason": "기술 요건 대비 수행실적 부족. 경쟁 우위 확보 어려움.",
  "feedback": "다음 유사 공고 시 재검토",
  "approved_by": "김팀장"
}

// STEP 1-②: Go/No-Go 재검토 요청 (go_no_go 노드 재실행)
{
  "decision": "rejected",
  "feedback": "수행실적 중 유사 프로젝트 누락 확인. 재평가 필요."
}

// STEP 2: 전략 승인 + 대안 선택 (D-6)
{
  "approved": true,
  "selected_alt_id": "A",
  "approved_by": "홍길동"
}

// STEP 2: 포지셔닝 변경 (D-2)
{
  "approved": false,
  "positioning_override": "adjacent",
  "feedback": "분석 결과 인접형이 더 적절. 유사 실적이 있으므로."
}

// STEP 3: 부분 재작업 (D-1)
{
  "approved": false,
  "feedback": "입찰가격 전략 수정 필요. 나머지는 양호.",
  "rework_targets": ["plan_price"],
  "comments": {
    "plan_price": "경쟁사 예상 가격 대비 15% 높음. 재검토 필요."
  }
}

// STEP 4: 부분 재작업 (D-1)
{
  "approved": false,
  "feedback": "수행방안 섹션 보강 필요.",
  "rework_targets": ["approach"],
  "comments": {
    "approach": "기술 아키텍처 다이어그램이 빠져 있음"
  }
}
```

### 12-3. 영향 범위 조회 API (U-5)

```json
// GET /api/proposals/{id}/impact/strategy
// → STEP 2를 재작업하면 영향받는 범위
{
  "target_step": "strategy",
  "affected_steps": [
    { "step": "plan",     "status": "approved", "will_reset": true },
    { "step": "proposal", "status": "approved", "will_reset": true },
    { "step": "ppt",      "status": "pending",  "will_reset": false }
  ],
  "warning": "STEP 3(제안계획)과 STEP 4(정성제안서)의 승인이 초기화됩니다. 재작업이 필요합니다."
}
```

### 12-4. 산출물 / G2B / 역량 DB

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/api/proposals/{id}/artifacts/{step}` | 산출물 조회 |
| GET  | `/api/proposals/{id}/artifacts/{step}/versions` | 버전 이력 |
| GET  | `/api/proposals/{id}/download/docx` | DOCX 다운로드 (**중간 버전 포함**, U-9) |
| GET  | `/api/proposals/{id}/download/pptx` | PPTX 다운로드 |
| GET  | `/api/proposals/{id}/compliance` | Compliance Matrix 현재 상태 |
| GET  | `/api/g2b/search` | 공고 검색 |
| GET  | `/api/g2b/bid/{bid_no}` | 낙찰정보 |
| GET  | `/api/g2b/stats` | 유사 공고 낙찰 통계 |
| GET  | `/api/capabilities` | 역량 목록 |
| POST | `/api/capabilities` | 역량 등록 |
| PUT  | `/api/capabilities/{id}` | 역량 수정 |
| DELETE | `/api/capabilities/{id}` | 역량 삭제 |
| GET  | `/api/capabilities/search` | 키워드 검색 |
| POST | `/api/proposals/{id}/artifacts/{step}/sections/{section_id}/regenerate` | ★ v3.4: 개별 섹션 AI 재생성 (H1) |
| POST | `/api/proposals/{id}/ai-assist` | ★ v3.4: AI 어시스턴트 인라인 제안 (H2) |
| GET  | `/api/proposals/{id}/evaluation` | ★ v3.4: 모의평가 결과 조회 (H3) |
| GET  | `/api/proposals/{id}/artifacts/{step}/diff?v1=N&v2=M` | ★ v3.4: 버전 간 Diff 조회 (M2) |
| GET  | `/api/proposals/{id}/download/hwp` | ★ v3.4: HWP 내보내기 (M3) |

#### 12-4-1. ★ 섹션 AI 재생성 API (v3.4, H1)

> **용도**: §13-10 ProposalEditor의 "AI에게 질문하기" 기능. 기존 `/resume`은 전체 단계 재작업만 가능하므로, 개별 섹션 단위 AI 재생성 엔드포인트 필요.

```python
# POST /api/proposals/{id}/artifacts/{step}/sections/{section_id}/regenerate
# 권한: 프로젝트 참여자 (member, lead)
# 섹션 잠금 보유자만 호출 가능 (SECT_001 에러)
```

```json
// Request
{
  "instruction": "경쟁사 대비 기술적 차별점을 더 구체적으로 서술해주세요.",
  "context": {
    "reference_sections": ["approach", "team"],
    "kb_search_query": "AI 플랫폼 차별화 전략"
  }
}

// Response — 200 OK
{
  "section_id": "technical_approach",
  "content": "...(재생성된 섹션 내용)...",
  "change_source": "ai_revised",
  "tokens_used": 3200,
  "kb_references": [
    {"type": "content_library", "id": "uuid-1", "title": "AI 플랫폼 제안 사례"}
  ]
}
```

#### 12-4-2. ★ AI 어시스턴트 인라인 제안 API (v3.4, H2)

> **용도**: §13-10 EditorAiPanel의 "선택 텍스트 개선 요청". H1(전체 섹션 재생성)과 달리 선택한 텍스트 조각에 대한 경량 호출.

```python
# POST /api/proposals/{id}/ai-assist
# 권한: 프로젝트 참여자 (member, lead)
```

```json
// Request
{
  "section_id": "technical_approach",
  "selected_text": "본 과업은 AI 기술을 활용하여 업무 효율을 높입니다.",
  "instruction": "더 구체적인 수치와 기술 명칭을 포함해 개선",
  "tone": "formal"
}

// Response — 200 OK
{
  "original_text": "본 과업은 AI 기술을 활용하여 업무 효율을 높입니다.",
  "suggested_text": "본 과업은 자연어처리(NLP) 기반 문서 자동 분류 및 RAG(Retrieval-Augmented Generation) 기술을 적용하여, 기존 수작업 대비 문서 처리 시간을 약 60% 단축합니다.",
  "tokens_used": 850,
  "change_type": "enhancement"
}
```

#### 12-4-3. ★ 모의평가 결과 조회 API (v3.4, H3)

> **용도**: §13-11 EvaluationView가 `evaluation_simulation` 데이터(3인 점수, 취약점, Q&A) 필요. 현재 graph state에만 존재하며 REST 엔드포인트 없음.

```python
# GET /api/proposals/{id}/evaluation
# 권한: 프로젝트 참여자 + 팀장/본부장 (결재선 포함)
```

```json
// Response — 200 OK
{
  "proposal_id": "uuid-123",
  "evaluation_at": "2026-03-10T15:00:00Z",
  "evaluators": [
    {
      "persona": "기술 전문가",
      "scores": {
        "technical_approach": 85,
        "project_management": 78,
        "team_composition": 90,
        "price_competitiveness": 72,
        "past_performance": 88
      },
      "total_score": 82.6,
      "comments": "기술적 접근은 우수하나 가격 경쟁력 보완 필요"
    },
    {
      "persona": "발주기관 담당자",
      "scores": { "...": "..." },
      "total_score": 79.2,
      "comments": "RFP 요구사항 대비 충족도 양호"
    },
    {
      "persona": "경쟁사 평가자",
      "scores": { "...": "..." },
      "total_score": 76.8,
      "comments": "차별화 포인트 부족"
    }
  ],
  "average_score": 79.5,
  "weaknesses_top3": [
    {"area": "price_competitiveness", "detail": "경쟁사 예상 가격 대비 12% 높음", "suggestion": "간접비 항목 재검토"},
    {"area": "differentiation", "detail": "기술적 차별화 포인트 불명확", "suggestion": "AI/ML 특화 역량 강조"},
    {"area": "risk_management", "detail": "리스크 대응 계획 미흡", "suggestion": "유사 프로젝트 교훈 반영"}
  ],
  "expected_qa": [
    {"question": "AI 모델 학습 데이터의 보안 관리 방안은?", "suggested_answer": "..."},
    {"question": "기존 시스템과의 연동 테스트 계획은?", "suggested_answer": "..."}
  ]
}
```

#### 12-4-4. ★ 버전 간 Diff 조회 API (v3.4, M2)

> **용도**: DB에 `diff_from_previous` JSONB 있지만, 임의 버전 간 비교를 위한 엔드포인트. 인접 버전 외 v1↔v3 등 교차 비교 지원.

```python
# GET /api/proposals/{id}/artifacts/{step}/diff?v1=2&v2=5
# 권한: 프로젝트 참여자
```

```json
// Response — 200 OK
{
  "step": "proposal",
  "version_from": 2,
  "version_to": 5,
  "sections_changed": [
    {
      "section_id": "technical_approach",
      "change_type": "modified",
      "additions": 12,
      "deletions": 5,
      "diff_html": "<ins>추가된 내용</ins><del>삭제된 내용</del>"
    }
  ],
  "summary": "3개 섹션 수정, 1개 섹션 추가"
}
```

#### 12-4-5. ★ HWP 내보내기 (v3.4, M3)

> **용도**: 한국 공공조달 제안서의 HWP 포맷 지원. 별도 설계문서(`hwp-output.design.md`) 참조. §12-4 인덱스에 추가.

```python
# GET /api/proposals/{id}/download/hwp
# 권한: 프로젝트 참여자
# 응답: application/octet-stream (HWP 바이너리)
# 파라미터: ?template_id=uuid (선택, 회사 HWP 템플릿 적용)
```

---

### 12-6. ★ 인증 API (v2.0)

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/api/auth/login` | Azure AD SSO 로그인 리다이렉트 |
| GET  | `/api/auth/callback` | Azure AD OAuth 콜백 → Supabase 세션 생성 |
| POST | `/api/auth/refresh` | JWT 토큰 갱신 |
| POST | `/api/auth/logout` | 세션 종료 |
| GET  | `/api/auth/me` | 현재 사용자 정보 (역할·소속 포함) |

### 12-7. ★ 사용자·조직 관리 API (v2.0)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET  | `/api/users` | 사용자 목록 | admin |
| GET  | `/api/users/{id}` | 사용자 상세 | admin, self |
| PUT  | `/api/users/{id}/role` | 역할 변경 | admin |
| GET  | `/api/organizations` | 조직 구조 (본부·팀) | admin |
| POST | `/api/organizations/divisions` | 본부 생성 | admin |
| POST | `/api/organizations/teams` | 팀 생성 | admin |
| PUT  | `/api/organizations/teams/{id}` | 팀 수정 (소속 변경 등) | admin |
| GET  | `/api/teams/{id}/members` | 팀원 목록 | lead, admin |
| POST | `/api/proposals/{id}/participants` | 프로젝트 참여자 배정 | lead |
| DELETE | `/api/proposals/{id}/participants/{user_id}` | 참여자 제외 | lead |

### 12-8. ★ 대시보드 API (v2.0)

| Method | Path | 설명 | 대상 역할 |
|--------|------|------|-----------|
| GET  | `/api/dashboard/my-projects` | 내 참여 프로젝트 현황 | member |
| GET  | `/api/dashboard/team` | 팀 제안 파이프라인 (STEP별 분포) | lead |
| GET  | `/api/dashboard/team/performance` | 팀 성과 요약 (수주율·건수) | lead |
| GET  | `/api/dashboard/division` | 본부 제안 현황 (팀별 비교) | director |
| GET  | `/api/dashboard/division/approvals` | 결재 대기 건 목록 | director |
| GET  | `/api/dashboard/company` | 전사 제안 현황 | executive |
| GET  | `/api/dashboard/company/kpi` | 전사 KPI (수주율 추이·분야 분석) | executive |
| GET  | `/api/dashboard/admin/stats` | 시스템 통계 (사용자·프로젝트 수) | admin |

### 12-9. ★ 성과 추적 API (v2.0)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals/{id}/result` | 제안 결과 등록 (수주/패찰/유찰) — 팀장 |
| GET  | `/api/performance/individual/{user_id}` | 개인 성과 (참여·완료·수주 건수) |
| GET  | `/api/performance/team/{team_id}` | 팀 성과 (수주율·건수·평균 소요일) |
| GET  | `/api/performance/division/{div_id}` | 본부 성과 (수주율·누적 수주액) |
| GET  | `/api/performance/company` | 전사 성과 (포지셔닝별 수주율) |
| GET  | `/api/performance/trends` | 기간별 추이 (월/분기/연, 필터 가능) |

### 12-10. ★ 알림 API (v2.0)

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/api/notifications` | 내 알림 목록 (읽음/안읽음) |
| PUT  | `/api/notifications/{id}/read` | 알림 읽음 처리 |
| PUT  | `/api/notifications/read-all` | 전체 읽음 처리 |
| GET  | `/api/notifications/settings` | 알림 설정 조회 |
| PUT  | `/api/notifications/settings` | 알림 설정 변경 (ON/OFF, 채널) |

### 12-11. ★ 감사 로그 API (v2.0)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET  | `/api/audit-logs` | 감사 로그 조회 (기간·사용자·행위 필터) | admin |

### 12-12. ★ v3.0 추가 API (교차 참조)

> 아래 API들은 각 설계 섹션에서 상세히 정의됨. 요약 인덱스만 제공.

| 영역 | API 그룹 | 상세 섹션 |
|------|----------|-----------|
| KB 콘텐츠 라이브러리 | `GET/POST/PUT/DELETE /api/kb/content/*` | §20-4 |
| KB 발주기관 DB | `GET/POST/PUT /api/kb/clients/*` | §20-4 |
| KB 경쟁사 DB | `GET/POST/PUT /api/kb/competitors/*` | §20-4 |
| KB 교훈 아카이브 | `GET/POST /api/kb/lessons/*` | §20-4 |
| KB 통합 검색 | `GET /api/kb/search` | §20-4 |
| KB 내보내기 | `GET /api/kb/export/{part}` | §20-4 |
| AI 실행 상태 | `GET/POST/DELETE /api/ai-status/*` | §22 |
| 동시 편집 잠금 | `POST/DELETE/GET /api/proposals/{id}/sections/*/lock` | §24 |
| 회사 템플릿 | `GET/POST/PUT/DELETE /api/templates/*` | §26 |
| 사용자 관리 (v3.0 확장) | `POST /api/users/bulk`, `PUT /api/users/{id}/deactivate`, `POST /api/users/{id}/delegate` | §23 |
| KB 원가기준 (노임단가) ★ v3.4 | `GET/POST/PUT/DELETE /api/kb/labor-rates`, `POST /api/kb/labor-rates/import` | §13-13, §15-5h |
| KB 낙찰가 벤치마크 ★ v3.4 | `GET/POST/PUT/DELETE /api/kb/market-prices` | §13-13, §15-5i |

### 12-5. SSE 클라이언트 자동 재연결 (U-6)

```typescript
// frontend/lib/sse.ts
export function createSSEClient(proposalId: string) {
  let retryCount = 0;
  const MAX_RETRIES = 5;

  function connect() {
    const es = new EventSource(`/api/proposals/${proposalId}/stream`);

    es.onmessage = (event) => {
      retryCount = 0;  // 성공 시 리셋
      const data = JSON.parse(event.data);
      // 프론트엔드 상태 업데이트
      handleStreamEvent(data);
    };

    es.onerror = () => {
      es.close();
      if (retryCount < MAX_RETRIES) {
        retryCount++;
        // 지수 백오프 재연결
        setTimeout(connect, Math.min(1000 * 2 ** retryCount, 30000));
      } else {
        // 재연결 실패 → GET /state 로 현재 상태 복원
        fetchCurrentState(proposalId);
      }
    };

    return es;
  }

  return connect();
}
```

### 12-13. ★ 분석 대시보드 API (v3.4)

> **용도**: §13-12 AnalyticsPage의 4개 차트 데이터 소스. 기존 §12-8(대시보드)/§12-9(성과 추적)는 역할별 원시 데이터 제공이며, 차트에 필요한 집계(aggregation) API가 없음.

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/analytics/failure-reasons?period=2026Q1` | 실패 원인 분포 (파이 차트) |
| GET | `/api/analytics/positioning-win-rate?period=2026Q1` | 포지셔닝별 수주율 (바 차트) |
| GET | `/api/analytics/monthly-trends?from=2025-10&to=2026-03` | 월별 수주율 추이 (라인 차트) |
| GET | `/api/analytics/client-win-rate?period=2026Q1` | 기관별 수주 현황 (바 차트) |

> **권한**: lead, director, executive, admin. member는 자신이 참여한 프로젝트 범위 내에서만 조회 가능.
> **기간 파라미터**: `period` = `2026Q1`, `2026H1`, `2025` 형식. `from`/`to` = `YYYY-MM` 형식.
> **스코프**: `?scope=team|division|company` (기본값: 사용자 역할에 따라 자동 결정)

#### Response 예시

```json
// GET /api/analytics/failure-reasons?period=2026Q1
{
  "period": "2026Q1",
  "scope": "company",
  "total_failed": 12,
  "reasons": [
    {"reason": "가격 경쟁력 부족", "count": 5, "percentage": 41.7},
    {"reason": "기술 제안 미흡", "count": 3, "percentage": 25.0},
    {"reason": "수행실적 부족", "count": 2, "percentage": 16.7},
    {"reason": "컨소시엄 구성 약점", "count": 1, "percentage": 8.3},
    {"reason": "기타/불명", "count": 1, "percentage": 8.3}
  ]
}

// GET /api/analytics/positioning-win-rate?period=2026Q1
{
  "period": "2026Q1",
  "scope": "company",
  "positionings": [
    {"positioning": "offensive", "total": 8, "won": 5, "win_rate": 62.5},
    {"positioning": "defensive", "total": 6, "won": 2, "win_rate": 33.3},
    {"positioning": "adjacent", "total": 4, "won": 3, "win_rate": 75.0},
    {"positioning": "exploratory", "total": 2, "won": 0, "win_rate": 0.0}
  ]
}
```

---
