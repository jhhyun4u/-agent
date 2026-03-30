# 제안 프로젝트 통합 워크플로우 설계 v5.0
## (기존 16개 + 신규 6개 → 10개 Business Status + 40개 LangGraph Phase)

> **작성일**: 2026-03-29
> **상태**: 검토 완료, 실구현 준비
> **갭 분석 결과**: 2-레이어 모델 권장 + CRITICAL 버그 발견
> **마이그레이션 기간**: 3일 (DB + 백엔드 + 프론트엔드)

---

## 🚨 CRITICAL 이슈 (즉시 수정 필요)

### Issue: DB CHECK constraint vs 실제 코드 불일치

**현황**:
- `routes_workflow.py:153`: `status = "running"` 저장 시도
- `routes_workflow.py:298`: `status = "cancelled"` 저장 시도
- `database/schema_v3.4.sql:117`: CHECK constraint에는 `running`, `cancelled` 없음

**결과**: PostgreSQL이 UPDATE 거부 → **500 Internal Error**

**해결**: 즉시 Step 1 DB 마이그레이션 실행 필요

---

## 📊 통합 워크플로우 아키텍처

### 3-레이어 구조

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Business Status (proposals.status, 10개)           │
│  ────────────────────────────────────────────────────────    │
│  사용자 및 현업이 보는 높은 수준의 프로젝트 단계              │
│                                                             │
│  waiting → in_progress → completed → submitted →           │
│           (no_go ↓)       ↓           ↓                    │
│           presentation ← ← ← → closed → archived           │
│                              ↑                              │
│  특수: on_hold (모든 활성 상태에서 진입 가능)                 │
│       expired (마감일 경과 시 자동 진입)                     │
│       abandoned (사용자 주도 중단)                           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Workflow Phase (proposals.current_phase, text)     │
│  ────────────────────────────────────────────────────────    │
│  LangGraph 40개 노드가 업데이트하는 세밀한 진행 단계         │
│                                                             │
│  HEAD: rfp_analyze → research → go_no_go → strategy        │
│  STEP 2: plan → proposal_write → self_review               │
│  STEP 3: ppt_generation                                    │
│  STEP 4: eval_result → project_closing                     │
│  PATH B: submission_docs → bidding (병렬)                   │
│                                                             │
│  예: current_phase='proposal_write_next'                     │
│       ↓ (LangGraph가 세션 중 자동 업데이트)                  │
│      current_phase='review_section'                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: AI Runtime Status (ai_task_status 테이블, 임시)    │
│  ────────────────────────────────────────────────────────    │
│  LangGraph 실행 중의 일시적 상태 (세션 종료 시 소멸)          │
│                                                             │
│  running (실행 중)                                           │
│  ├─ paused (사용자 중단)                                     │
│  ├─ error (AI 에러)                                         │
│  └─ no_response (타임아웃)                                  │
│                                                             │
│  예: 사용자가 제안서 작성 중 창을 닫으면              │
│      ai_task_status='paused' (Layer 3)                      │
│      proposals.status='in_progress' (Layer 1 유지)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 상태 매핑: 기존 16개 → 신규 10개

### 매핑 테이블

| # | 기존 상태 | 신규 Business Status | 신규 의미 | 처리 |
|---|----------|---------------------|----------|------|
| 1 | initialized | **waiting** | PM/PL 할당 전, 미시작 | 이름 변경 |
| 2-5 | processing, searching, analyzing, strategizing | **in_progress** | LangGraph 실행 중, current_phase로 구분 | 통합 |
| 6 | completed | **completed** | 작성 완료, 최종 검토 | 유지 |
| 7 | submitted | **submitted** | 제출 완료, 평가 대기 | 유지 |
| 8 | presented | **presentation** | 발표 준비/리허설 진행 | 이름 변경 |
| 9 | won | **closed** + `win_result='won'` | 수주됨 (closed의 세부값) | 통합 |
| 10 | lost | **closed** + `win_result='lost'` | 패찰됨 (closed의 세부값) | 통합 |
| 11 | no_go | **closed** + `win_result='no_go'` | 노고 (in_progress에서 즉시 종료) | 통합 |
| 12 | abandoned | **closed** + `win_result='abandoned'` | 사용자 중단 | 통합 |
| 13 | retrospect | ~~삭제~~ | closed 후 교훈 입력 활동 → proposal_timelines 이벤트로 추적 | 제거 |
| 14 | on_hold | **on_hold** | 비즈니스 보류 (모든 활성 상태에서 진입) | 유지 |
| 15 | expired | **expired** | 마감일 경과 (자동 진입, closed로 전환 가능) | 유지 |
| FE | running | ~~삭제~~ | ai_task_status='running' (Layer 3로 분리) | 분리 |
| FE | failed | ~~삭제~~ | ai_task_status='error' (Layer 3로 분리) | 분리 |
| FE | cancelled | **closed** + `win_result='cancelled'` | 사용자 캔슬 | 통합 |
| FE | paused | ~~삭제~~ | ai_task_status='paused' (Layer 3로 분리) | 분리 |

### 최종 Business Status Enum (10개)

```python
class ProposalStatus(str, Enum):
    WAITING       = "waiting"        # 1. PM/PL 할당 대기
    IN_PROGRESS   = "in_progress"    # 2-5. 제안서 작성 진행 (current_phase로 세분화)
    COMPLETED     = "completed"      # 6. 작성 완료, 최종 검토
    SUBMITTED     = "submitted"      # 7. 제출 완료, 평가 대기
    PRESENTATION  = "presentation"   # 8. 발표 준비/리허설
    CLOSED        = "closed"         # 9-12, 15. 종료 (win_result로 세부 구분)
    ARCHIVED      = "archived"       # 16. 보관 (30일 후 자동)
    ON_HOLD       = "on_hold"        # 비즈니스 보류 (모든 활성 상태에서 진입)
    EXPIRED       = "expired"        # 마감일 경과 (closed로 전환)
    # (아래는 Layer 3로 분리)
    # RUNNING, PAUSED, FAILED → ai_task_status 테이블로 관리
```

### win_result Enum (closed 상태의 세부 구분)

```python
class WinResult(str, Enum):
    WON        = "won"         # 수주 (기존 won)
    LOST       = "lost"        # 패찰 (기존 lost)
    NO_GO      = "no_go"       # 노고 (기존 no_go)
    ABANDONED  = "abandoned"   # 중단 (기존 abandoned)
    CANCELLED  = "cancelled"   # 취소 (기존 FE cancelled)
    # Note: retrospect는 event로 변경, expired는 별도 상태
```

---

## 📐 상태 전환 규칙 (통합 후)

### 전환 다이어그램

```
초기 생성
    │
    ▼
  waiting ──────► on_hold (보류)
    │             ▲    │
    │             └────┘ (복귀)
    │
    ├─ (PM/PL 할당) ──────┐
    │                     │
    │                     ▼
    ├──────────────► in_progress
    │                     │
    │                ┌────┴──────┬─────────┐
    │                │           │         │
    │         (no_go 탈락)  (계속 작성)   (보류)
    │                │           │         │
    │                ▼           ▼         ▼
    │            closed      (계속)    on_hold
    │         (win_result    │          │
    │          =no_go)       ▼          └─┐
    │                   completed         │
    │                       │             │
    │                       ├─ (재작업)──┘
    │                       │
    │                       ▼
    │                   submitted
    │                       │
    │                  ┌────┴────────┐
    │                  │             │
    │           (탈락)  │        (평가대상)
    │                  │             │
    │                  ▼             ▼
    │             closed         presentation
    │        (win_result=lost)      │
    │                               │ (평가)
    │                          ┌────┴────────┐
    │                          │             │
    │                      (수주)│          (탈락)
    │                          ▼             ▼
    │                      closed        closed
    │                  (win_result=won) (win_result=lost)
    │                          │
    │                          ▼
    │                      (30일 경과)
    │                          │
    │                          ▼
    └──────────────────────► archived


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

특수 경로:

[마감일 경과]
  in_progress/completed → expired → closed(auto)

[사용자 중단]
  (활성 상태) → closed(win_result=abandoned)

[사용자 캔슬]
  (활성 상태) → closed(win_result=cancelled)
```

### 전환 규칙 테이블

| From | To | 조건 | 실행자 | 새 컬럼 |
|------|----|----|---------|--------|
| waiting | in_progress | PM/PL 할당 + 착수 버튼 | 사용자(PM) | `started_at=NOW()` |
| in_progress | completed | 모든 섹션 완료 + 자가진단 ≥70점 | 자동(LangGraph review_proposal) | `completed_at=NOW()` |
| in_progress | closed | Go/No-Go 탈락 | 자동(LangGraph go_no_go) | `closed_at=NOW()`, `win_result='no_go'` |
| in_progress | on_hold | PM 판단 | 사용자(PM) | (타임스탬프 없음) |
| in_progress | expired | 마감일 경과 | 자동(cron) | `expired_at=NOW()` |
| completed | submitted | 제출 확인 | 사용자(PM) | `submitted_at=NOW()` |
| completed | in_progress | 재작업 필요 | 사용자(PM) | (completed_at 유지, progress 재계산) |
| submitted | presentation | 발표 대상 확정 | 사용자(PM) | `presentation_started_at=NOW()` |
| submitted | closed | 서류 탈락 | 사용자(PM) | `closed_at=NOW()`, `win_result='lost'` |
| presentation | closed | 평가 결과 | 사용자(PM) | `closed_at=NOW()`, `win_result='won/lost'` |
| on_hold | in_progress | 보류 해제 | 사용자(PM) | (복귀, 타임스탬프 유지) |
| * (활성) | on_hold | 보류 | 사용자(PM) | (새 보류, 타임스탬프 없음) |
| * (활성) | closed | 중단 | 사용자(PM) | `closed_at=NOW()`, `win_result='abandoned/cancelled'` |
| closed | archived | 30일 경과 | 자동(cron) | `archived_at=NOW()` |

---

## 📋 스키마 설계

### 1. proposals 테이블 (확장)

```sql
CREATE TABLE proposals (
  -- [기존 PK/외래키]
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id),
  owner_id UUID REFERENCES users(id),

  -- [기존: 기본 정보]
  title TEXT NOT NULL,
  client_name TEXT,
  description TEXT,

  -- [신규: PM/PL (Phase 0)]
  project_manager_id UUID,
  project_leader_id UUID,

  -- [기존: 일정/입찰]
  deadline TIMESTAMPTZ NOT NULL,
  bid_amount BIGINT,

  -- ═══════════════════════════════════════════════════════════
  -- Layer 1: Business Status (신규 컬럼)
  -- ═══════════════════════════════════════════════════════════
  status VARCHAR(50) NOT NULL DEFAULT 'waiting',
    -- CHECK: waiting | in_progress | completed | submitted | presentation | closed | archived | on_hold | expired

  -- closed 상태의 세부값
  win_result VARCHAR(50),
    -- NULL | won | lost | no_go | abandoned | cancelled

  -- ═══════════════════════════════════════════════════════════
  -- Layer 2: Workflow Phase (기존 개선)
  -- ═══════════════════════════════════════════════════════════
  current_phase TEXT,
    -- LangGraph 노드 이름 (rfp_analyze, strategy_generate, proposal_write_next 등)
    -- props.metadata['current_step']과 동기화

  -- ═══════════════════════════════════════════════════════════
  -- Layer 1 타임스탬프 (신규)
  -- ═══════════════════════════════════════════════════════════
  started_at TIMESTAMP,          -- waiting → in_progress 시점
  completed_at TIMESTAMP,        -- in_progress → completed 시점
  submitted_at TIMESTAMP,        -- completed → submitted 시점
  presentation_started_at TIMESTAMP,  -- submitted → presentation 시점
  closed_at TIMESTAMP,           -- * → closed 시점
  archived_at TIMESTAMP,         -- closed → archived 시점 (30일 후)
  expired_at TIMESTAMP,          -- expired 진입 시점

  -- [기존: 기타]
  rfp_filename VARCHAR(500),
  rfp_content TEXT,
  storage_path_docx VARCHAR(500),
  storage_path_pptx VARCHAR(500),
  storage_path_hwpx VARCHAR(500),
  bid_confirmed_amount NUMERIC(15,2),
  bid_confirmed_date TIMESTAMP,
  positioning TEXT,  -- Go/No-Go 결과
  streams_ready BOOLEAN DEFAULT FALSE,
  submission_gate_status VARCHAR(50),
  is_archived BOOLEAN DEFAULT FALSE,
  archive_snapshot_at TIMESTAMP,

  -- [감사]
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- ═══════════════════════════════════════════════════════════
  -- 제약 조건
  -- ═══════════════════════════════════════════════════════════
  CONSTRAINT status_check CHECK (
    status IN ('waiting','in_progress','completed','submitted',
               'presentation','closed','archived','on_hold','expired')
  ),
  CONSTRAINT win_result_check CHECK (
    win_result IS NULL OR
    win_result IN ('won','lost','no_go','abandoned','cancelled')
  ),
  CONSTRAINT status_win_result_check CHECK (
    (status = 'closed' AND win_result IS NOT NULL) OR
    (status != 'closed' AND win_result IS NULL)
  ),
  CONSTRAINT date_chain_check CHECK (
    (started_at IS NULL OR started_at >= created_at) AND
    (completed_at IS NULL OR completed_at >= started_at) AND
    (submitted_at IS NULL OR submitted_at >= completed_at) AND
    (presentation_started_at IS NULL OR presentation_started_at >= submitted_at) AND
    (closed_at IS NULL OR closed_at >= GREATEST(presentation_started_at, submitted_at, started_at)) AND
    (archived_at IS NULL OR archived_at > closed_at)
  )
);

-- 인덱스
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_status_win_result ON proposals(status, win_result);
CREATE INDEX idx_proposals_archived ON proposals(is_archived, archived_at);
CREATE INDEX idx_proposals_deadline ON proposals(deadline);
```

### 2. proposal_timelines (신규)

```sql
CREATE TABLE proposal_timelines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  event_type VARCHAR(50) NOT NULL,
    -- ENUM: created, assigned_pm, assigned_pl, started, section_completed,
    --       phase_completed, completed, submitted, presentation_started,
    --       closed (with win_result), archived, on_hold_entered, on_hold_exited,
    --       expired, retrospect (lesson recorded)

  event_description TEXT,

  status_before VARCHAR(50),     -- 이전 status
  status_after VARCHAR(50),      -- 새 status
  win_result_after VARCHAR(50),  -- closed 시 새 win_result

  triggered_by UUID NOT NULL REFERENCES users(id),
  triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  metadata JSONB,  -- 추가 정보: phase, score, lesson_text, reason 등

  FOREIGN KEY (proposal_id) REFERENCES proposals(id)
);

CREATE INDEX idx_proposal_timelines_proposal ON proposal_timelines(proposal_id);
CREATE INDEX idx_proposal_timelines_event ON proposal_timelines(event_type);
```

### 3. ai_task_status (신규, Layer 3)

```sql
CREATE TABLE ai_task_status (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
  session_id VARCHAR(255) NOT NULL,  -- LangGraph checkpoint ID

  status VARCHAR(50) NOT NULL,
    -- ENUM: running | paused | error | no_response | complete

  error_message TEXT,
  error_code VARCHAR(50),
  retry_count INT DEFAULT 0,
  max_retries INT DEFAULT 3,

  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,

  -- TTL (자동 정리)
  expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),

  FOREIGN KEY (proposal_id) REFERENCES proposals(id)
);

CREATE INDEX idx_ai_task_status_proposal ON ai_task_status(proposal_id);
CREATE INDEX idx_ai_task_status_expires ON ai_task_status(expires_at);
```

---

## 🔌 LangGraph 노드 매핑

### current_phase 값 정의

| Phase Group | current_phase 값 | 해당 Business Status |
|-------------|------------------|---------------------|
| **HEAD** | | |
| | `rfp_analyze` | in_progress |
| | `research_gather` | in_progress |
| | `go_no_go` | in_progress (또는 → closed if no_go) |
| | `go_no_go_review` | in_progress |
| | `strategy_generate` | in_progress |
| | `strategy_review` | in_progress |
| **PLAN** | | |
| | `plan_team` | in_progress |
| | `plan_assign` | in_progress |
| | `plan_schedule` | in_progress |
| | `plan_story` | in_progress |
| | `plan_price` | in_progress |
| | `plan_merge` | in_progress |
| | `plan_review` | in_progress |
| **PROPOSAL** | | |
| | `proposal_start_gate` | in_progress |
| | `proposal_write_next` | in_progress |
| | `review_section` | in_progress |
| | `self_review` | in_progress |
| | `review_proposal` | in_progress → completed |
| **PPT** | | |
| | `presentation_strategy` | in_progress |
| | `ppt_toc` | in_progress |
| | `ppt_visual_brief` | in_progress |
| | `ppt_storyboard` | in_progress |
| | `review_ppt` | in_progress |
| **EVAL** | | |
| | `mock_evaluation` | in_progress |
| | `review_mock_eval` | in_progress |
| | `eval_result` | in_progress → closed |
| | `project_closing` | in_progress → closed |
| **PATH B** | | |
| | `submission_docs_plan` | in_progress |
| | `bid_plan` | in_progress |
| | `cost_sheet_generate` | in_progress |
| | `submission_checklist` | in_progress |
| | `convergence_gate` | in_progress |

### 상태 자동 계산

```
Layer 1: status = proposals.status (명시적 UPDATE)
Layer 2: current_phase = proposals.current_phase (LangGraph 자동 업데이트)
Layer 3: ai_task_status.status = ai_status_manager 기록

사용자가 본다:
  ┌─ status=in_progress ──┐
  │                       ├─ UI에 "진행 중" 표시
  │ current_phase=        │
  │   proposal_write_next │
  └─ ai_task_status=      ┘
      running

  ↓

  사용자 인터페이스:
    제안서 작성 중... (Phase 4/5: 제안서 본문 작성)
```

---

## 📡 API 엔드포인트

### v2 엔드포인트 (신규, Layer 1 중심)

```
POST   /api/v2/proposals                 # 생성 (status='waiting')
GET    /api/v2/proposals                 # 목록 (status 필터)
GET    /api/v2/proposals/{id}            # 단건
PUT    /api/v2/proposals/{id}            # 수정 (waiting/in_progress/completed만)
DELETE /api/v2/proposals/{id}            # 삭제 (waiting만)

POST   /api/v2/proposals/{id}/assign-pm  # PM 할당
POST   /api/v2/proposals/{id}/assign-pl  # PL 할당

POST   /api/v2/proposals/{id}/start      # waiting → in_progress
POST   /api/v2/proposals/{id}/complete   # in_progress → completed
POST   /api/v2/proposals/{id}/submit     # completed → submitted
POST   /api/v2/proposals/{id}/present    # submitted → presentation
POST   /api/v2/proposals/{id}/close      # * → closed

GET    /api/v2/proposals/{id}/progress   # 진행률 (current_phase 기반)
GET    /api/v2/proposals/{id}/timeline   # 생애주기 이벤트

POST   /api/v2/proposals/{id}/hold       # * → on_hold
POST   /api/v2/proposals/{id}/resume     # on_hold → 이전 상태

GET    /api/v2/proposals?status=&page=   # 필터 및 페이징
GET    /api/v2/proposals/archived        # 보관함 (is_archived=true)
```

### v1 엔드포인트 (기존, Layer 2/3 중심)

```
POST   /api/proposals/from-rfp           # RFP 업로드 (LangGraph 시작)
POST   /api/proposals/from-bid           # 공고 ID (LangGraph 시작)
POST   /api/proposals/{id}/start         # LangGraph 워크플로우 실행
POST   /api/proposals/{id}/resume        # 중단된 체크포인트 재개
GET    /api/proposals/{id}/stream        # SSE (현재 상태 스트리밍)
GET    /api/proposals/{id}/history       # 체크포인트 이력
POST   /api/proposals/{id}/goto/{step}   # Time-travel
```

**중요**: v1과 v2 `/start`는 다른 의미
- v1: LangGraph 워크플로우 **실행** (Layer 2/3)
- v2: Business status waiting **→** in_progress (Layer 1)

---

## 🗄️ 마이그레이션 체크리스트

### Step 1. DB 마이그레이션 (1일)

```sql
-- 018_status_unification.sql (1.5시간 소요)

-- (1) 신규 컬럼 추가
ALTER TABLE proposals ADD COLUMN win_result VARCHAR(50);
ALTER TABLE proposals ADD COLUMN started_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN completed_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN submitted_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN presentation_started_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN closed_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN archived_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN expired_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN project_manager_id UUID;
ALTER TABLE proposals ADD COLUMN project_leader_id UUID;

-- (2) 신규 테이블 생성
CREATE TABLE proposal_timelines (...);
CREATE TABLE ai_task_status (...);

-- (3) 데이터 마이그레이션
BEGIN;
UPDATE proposals SET status = 'in_progress'
  WHERE status IN ('processing','searching','analyzing','strategizing');
UPDATE proposals SET status = 'waiting' WHERE status = 'initialized';
UPDATE proposals SET status = 'presentation' WHERE status = 'presented';
UPDATE proposals SET win_result = 'won', status = 'closed' WHERE status = 'won';
UPDATE proposals SET win_result = 'lost', status = 'closed' WHERE status = 'lost';
UPDATE proposals SET win_result = 'no_go', status = 'closed' WHERE status = 'no_go';
UPDATE proposals SET win_result = 'abandoned', status = 'closed' WHERE status = 'abandoned';
UPDATE proposals SET status = 'closed' WHERE status = 'retrospect';
-- (on_hold, expired는 이미 존재)
COMMIT;

-- (4) CHECK constraint 교체
ALTER TABLE proposals DROP CONSTRAINT proposals_status_check;
ALTER TABLE proposals ADD CONSTRAINT status_check CHECK (...);
ALTER TABLE proposals ADD CONSTRAINT win_result_check CHECK (...);
ALTER TABLE proposals ADD CONSTRAINT status_win_result_check CHECK (...);

-- (5) 인덱스
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_status_win_result ON proposals(status, win_result);
```

### Step 2. 백엔드 수정 (1일)

- [ ] `app/models/types.py`: ProposalStatus enum 10개로 축소, WinResult enum 추가
- [ ] `app/graph/nodes/evaluation_nodes.py`: `status = "won"/"lost"` → `status = "closed"`, `win_result = 값`
- [ ] `app/graph/state.py`: ProposalState에 win_result, *_at 타임스탐프 필드 추가
- [ ] `app/api/routes_proposal.py`:
  - `_STATUS_GROUPS` 딕셔너리 제거
  - 상태 필터 쿼리 단순화 (`status = 값` 으로 변경)
  - v2 라우터 분리 생성
- [ ] `app/api/routes_workflow.py`:
  - `status = "running"/"cancelled"` → ai_task_status 테이블에 기록
  - Layer 3 상태 관리 분리
- [ ] `app/services/`: TimelineService 신규 (상태 전환 이벤트 기록)
- [ ] `database/migrations/`: 008_3-stream + 016_go_no_go 영향 재검토

### Step 3. 프론트엔드 수정 (0.5일)

- [ ] `frontend/lib/api.ts`: ProposalStatus 타입 10개로 축소
- [ ] AI 상태 별도 타입: `AiTaskStatus` (running/paused/error)
- [ ] 상태 표시 컴포넌트: `closed` + `win_result` 조합
- [ ] 모든 상태 필터링 로직 업데이트

### Step 4. 테스트 및 검증 (0.5일)

- [ ] 기존 MV 쿼리 업데이트 (004_performance_views.sql)
- [ ] E2E 테스트: 상태 전환 7개 시나리오
- [ ] 기존 데이터 검증: 마이그레이션 후 데이터 무결성 확인

**총 소요: 3일**

---

## ✅ 최종 상태 요약

| 항목 | 기존 | 신규 | 효과 |
|------|------|------|------|
| Business Status | 16개 (혼재) | 10개 (명확) | 사용자 이해도 ↑ |
| 쿼리 복잡도 | `IN ('processing',...5개)` | `= 'in_progress'` | 성능 ↑ |
| 세부 추적 | 16개 값 | current_phase + win_result | 유연성 ↑ |
| AI 상태 | status에 혼재 | Layer 3 분리 | 관심사 분리 ↑ |
| 체크섬 버그 | running/cancelled 미등록 | 고정 | 안정성 ↑ |

---

## 📌 중요 구현 노트

### 1. Layer 1과 Layer 2의 동기화

```python
# LangGraph 노드에서 (Layer 2 업데이트)
state.current_phase = "proposal_write_next"
await state.save_to_db()  # proposals.current_phase 업데이트

# 사용자 UI에서 (Layer 1 업데이트)
POST /api/v2/proposals/{id}/complete
→ UPDATE proposals SET status='completed', completed_at=NOW()

# 둘은 독립적으로 작동
```

### 2. on_hold와 expired의 특수성

```
on_hold (비즈니스 보류):
  - 모든 활성 상태에서 진입 가능
  - 보류 해제 후 이전 상태로 자동 복귀
  - 타임스탬프 기록 안 함 (상태 변경이 아니라 플래그)

expired (마감일 경과):
  - CRON job이 자동 진입
  - 자동으로 closed(win_result=null)로 전환
  - expired_at 타임스탬프 기록
```

### 3. no_go의 단축 경로

```
in_progress에서 go_no_go 노드 실행:
  ├─ go_no_go_gate
  │  ├─ YES (GO) → strategy 계속
  │  └─ NO (NO-GO) → status='closed', win_result='no_go', closed_at=NOW()
  │                   (proposal_writing 단계 스킵, 즉시 종료)

타임라인:
  created_at → started_at → (go_no_go) → closed_at
               (in_progress)      (closed)
```

---

## 🚀 롤아웃 계획

### Phase 1 (즉시, 2시간)
**CRITICAL**: DB CHECK constraint 수정
```sql
ALTER TABLE proposals ADD CONSTRAINT status_check CHECK (
  status IN ('initialized','processing','searching','analyzing','strategizing',
             'submitted','presented','won','lost','no_go','on_hold','expired',
             'abandoned','retrospect','completed','running','cancelled','failed','paused')
);
```

### Phase 2 (Week 1)
완전한 DB + 백엔드 마이그레이션 (3일)

### Phase 3 (Week 2)
프론트엔드 마이그레이션 + E2E 테스트 (2-3일)

### Phase 4 (Week 3)
프로덕션 배포 + 모니터링

