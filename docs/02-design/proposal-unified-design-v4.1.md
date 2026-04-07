# 제안 프로젝트 상태 시스템 - 통합 설계 v4.1
## (기존 구현과 신규 설계 병합)

> **작성일**: 2026-03-29
> **상태**: 검토 및 조정 완료
> **갭 분석 결과**: 30% 일치도 → 통합 전략 수립
> **권장 방식**: Option A - Incremental Migration (기존 LangGraph 워크플로우 보존 + 비즈니스 라이프사이클 레이어 추가)

---

## 📌 핵심 설계 결정

### 1. 이중 상태 모델 (Dual Status Model)

기존 세밀한 워크플로우 상태와 새로운 비즈니스 라이프사이클을 **병행 관리**:

```
┌─────────────────────────────────────────────────────────────────┐
│  비즈니스 라이프사이클 (Lifecycle Status) - 신규            │
│  ┌──────┐  ┌──────────────┐  ┌─────────┐  ┌────────┐  ┌─────┐ │
│  │대기  │→│ 진행 중       │→│ 완료됨  │→│ 제출됨 │→│발표 │ │
│  │wait  │  │in_progress   │  │completed│  │subm...│  │pres.│ │
│  └──────┘  └──────────────┘  └─────────┘  └────────┘  └─────┘ │
│                                                               │ │
│                                                    ┌──────────┘ │
│                                                    │            │
│                                                    ↓            │
│                                                  ┌────────┐    │
│                                                  │종료됨  │    │
│                                                  │closed  │    │
│                                                  └────────┘    │
│                                                       ↓         │
│                                                  [30일 경과]    │
│                                                       ↓         │
│                                                  ┌────────┐    │
│                                                  │보관    │    │
│                                                  │archived│    │
│                                                  └────────┘    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  워크플로우 단계 (Workflow Step) - 기존 LangGraph 유지      │
│  (RFP 검색→분석→전략→계획→섹션작성→평가→발표 등 40개 노드) │
│  표시: status='processing', 'searching', 'analyzing' 등     │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 컬럼 매핑 전략

**신규 추가 컬럼** (기존 유지):
```sql
ALTER TABLE proposals ADD COLUMN lifecycle_status VARCHAR(50) DEFAULT 'waiting';
ALTER TABLE proposals ADD COLUMN project_manager_id UUID;
ALTER TABLE proposals ADD COLUMN project_leader_id UUID;
ALTER TABLE proposals ADD COLUMN started_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN completed_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN submitted_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN closed_at TIMESTAMP;

-- 기존 컬럼 계속 사용
-- status (기존) -> 워크플로우 단계 유지
-- title -> project_name (alias로 대응)
-- owner_id -> created_by (alias)
-- current_phase (TEXT) -> phase 계산 필드로 변환
```

**기존 컬럼 매핑**:
| 신규 설계 | 기존 컬럼 | 방식 |
|------|------|------|
| `project_name` | `title` | Pydantic `alias` |
| `created_by` | `owner_id` | Pydantic `alias` |
| `bid_price` | `bid_amount` | Type conversion (BIGINT→DECIMAL) |
| `deadline_date` | `deadline` (TIMESTAMPTZ) | Type conversion 또는 새 컬럼 |
| `progress_percentage` | computed | `(completed_sections / total_sections) * 100` |
| `evaluation_result` | `win_result` | Enum mapping (수주→awarded, 패찰→rejected) |

---

## 🏗️ 통합 스키마

### 1. proposals 테이블 (확장)

```sql
CREATE TABLE IF NOT EXISTS proposals (
  -- [기존 PK/외래키]
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id),
  owner_id UUID REFERENCES users(id),  -- 기존: 생성자

  -- [기존: 제안 기본 정보]
  title TEXT NOT NULL,                           -- 신규 alias: project_name
  client_name TEXT,
  description TEXT,
  bid_amount BIGINT,                             -- 신규 alias: bid_price (decimal로 변환)

  -- [기존: RFP/파일 정보]
  rfp_filename VARCHAR(500),
  rfp_content TEXT,
  storage_path_docx VARCHAR(500),
  storage_path_pptx VARCHAR(500),
  storage_path_hwpx VARCHAR(500),

  -- [기존: 워크플로우 상태]
  status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    -- ENUM: initialized, processing, searching, analyzing, strategizing,
    --       submitted, presented, won, lost, no_go, on_hold, expired, abandoned, retrospect, completed
  current_phase TEXT,                            -- 신규 computed: phase (0-5)
  failed_phase VARCHAR(50),
  phases_completed INTEGER DEFAULT 0,

  -- [신규: 비즈니스 라이프사이클 상태]
  lifecycle_status VARCHAR(50) DEFAULT 'waiting',
    -- ENUM: waiting, in_progress, completed, submitted, presentation, closed, archived

  -- [신규: PM/PL 할당]
  project_manager_id UUID,                       -- PM (신규)
  project_leader_id UUID,                        -- PL (신규)

  -- [기존: 일정 정보]
  deadline TIMESTAMPTZ,                          -- 기존

  -- [신규: 생애주기 타임스탬프]
  started_at TIMESTAMP,                          -- in_progress 전환 시간
  completed_at TIMESTAMP,                        -- completed 전환 시간
  submitted_at TIMESTAMP,                        -- submitted 전환 시간
  closed_at TIMESTAMP,                           -- closed 전환 시간
  archived_at TIMESTAMP,                         -- archived 전환 시간 (30일 자동)

  -- [신규: 평가 정보]
  evaluation_result VARCHAR(50),                 -- awarded|rejected|disqualified
  evaluation_score INT,
  is_awarded BOOLEAN DEFAULT FALSE,

  -- [기존: 보관/아카이브]
  is_archived BOOLEAN DEFAULT FALSE,
  archive_snapshot_at TIMESTAMP,                 -- 기존

  -- [기존: 입찰/결과 정보]
  bid_no VARCHAR(100),
  bid_confirmed_amount NUMERIC(15,2),
  bid_confirmed_date TIMESTAMP,
  positioning TEXT,  -- Go/No-Go 결과

  -- [기존: 다중 스트림 워크플로우]
  streams_ready BOOLEAN DEFAULT FALSE,
  submission_gate_status VARCHAR(50),

  -- [감사]
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- [제약]
  CONSTRAINT valid_lifecycle_dates CHECK (
    (started_at IS NULL OR started_at >= created_at) AND
    (completed_at IS NULL OR completed_at >= started_at) AND
    (submitted_at IS NULL OR submitted_at >= completed_at) AND
    (closed_at IS NULL OR closed_at >= submitted_at) AND
    (archived_at IS NULL OR archived_at > COALESCE(closed_at, closed_at))
  ),
  CONSTRAINT valid_lifecycle_status CHECK (
    lifecycle_status IN ('waiting', 'in_progress', 'completed', 'submitted', 'presentation', 'closed', 'archived')
  ),
  CONSTRAINT valid_status CHECK (
    status IN ('initialized','processing','searching','analyzing','strategizing',
               'submitted','presented','won','lost','no_go','on_hold','expired',
               'abandoned','retrospect','completed')
  )
);
```

### 2. 신규 테이블 (추가)

#### 2a. proposal_timelines (생애주기 이벤트)
```sql
CREATE TABLE proposal_timelines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  event_type VARCHAR(50) NOT NULL,
    -- ENUM: created, assigned_pm, assigned_pl, started, section_completed,
    --       phase_completed, reviewed, submitted, presentation_started,
    --       awarded/rejected, closed, archived
  event_description TEXT,

  previous_lifecycle_status VARCHAR(50),
  new_lifecycle_status VARCHAR(50),
  previous_workflow_status VARCHAR(50),
  new_workflow_status VARCHAR(50),

  triggered_by UUID NOT NULL REFERENCES users(id),
  triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  metadata JSONB,  -- 추가 정보: phase, score, reason 등

  FOREIGN KEY (proposal_id) REFERENCES proposals(id)
);
```

#### 2b. proposal_team_members (팀원, 기존 확장)
```sql
-- 기존 project_participants 테이블 활용, 필요 시 확장
CREATE TABLE IF NOT EXISTS proposal_team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),

  role VARCHAR(50) NOT NULL,
    -- ENUM: pm, pl, writer, designer, reviewer, qa
  contribution_area VARCHAR(255),

  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  left_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,

  UNIQUE(proposal_id, user_id, role)
);
```

#### 2c. proposal_evaluations (평가 이력)
```sql
CREATE TABLE IF NOT EXISTS proposal_evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  evaluation_type VARCHAR(50) NOT NULL,
    -- ENUM: documentary_review, presentation, interview
  evaluation_date DATE,

  -- AI 자가진단 (4개축)
  self_assessment_score INT,  -- 0~100
  technical_score INT,
  organizational_score INT,
  commercial_score INT,

  -- 발주기관 평가
  client_evaluation_score INT,
  evaluation_result VARCHAR(50),  -- pending|qualified|shortlisted|awarded|rejected
  rejection_reason TEXT,

  evaluated_at TIMESTAMP,
  evaluated_by VARCHAR(255),

  notes JSONB,

  UNIQUE(proposal_id, evaluation_type),
  FOREIGN KEY (proposal_id) REFERENCES proposals(id)
);
```

---

## 🔄 라이프사이클 전환 규칙

### 상태 전환 매트릭스

```
현재 상태 → 다음 상태 | 조건 | 발생 이벤트 | created_by
---------|-----------|------|-----------|----------
waiting → in_progress | (1) PM+PL 할당 완료 (2) 착수 버튼 | started_at=NOW() | PM
in_progress → completed | (1) 모든 섹션 완료 (2) 자가진단 ≥70점 | completed_at=NOW() | PM
completed → submitted | 제출 버튼 | submitted_at=NOW() | PM
submitted → presentation | 평가대상 확정 | - | system (auto)
submitted → closed | 탈락/부적격 | closed_at=NOW(), is_awarded=false | system
presentation → closed | 발표 완료 | closed_at=NOW(), is_awarded=true/false | PM
closed → archived | [자동] 30일 경과 | archived_at=NOW(), is_archived=true | system (cron)
```

### 자동 전환 (자동화)

| 이벤트 | 조건 | 결과 | 구현 |
|--------|------|------|-----|
| PM+PL 할당 | `/assign-pm` + `/assign-pl` 모두 호출 | API 응답에 `canStart=true` 신호 | API 로직 |
| 섹션 완료 | 모든 섹션 status='approved' | `progress_percentage` 자동 계산 | Trigger 또는 API |
| 30일 자동 archive | CURRENT_DATE > closed_at + 30 | `lifecycle_status='archived'`, `is_archived=true` | Cron job (daily 00:00) |

---

## 📡 API 엔드포인트 (v2 경로)

### 기본 원칙
- **v1 경로**: 기존 `/api/proposals/` 유지 (LangGraph 워크플로우 중심)
- **v2 경로**: 새로운 `/api/v2/proposals/` (비즈니스 라이프사이클 중심)

### v2 Endpoints (신규)

#### 1. CRUD
```
POST   /api/v2/proposals                    # 생성
GET    /api/v2/proposals                    # 목록 (필터/페이징)
GET    /api/v2/proposals/{id}               # 단건 조회
PUT    /api/v2/proposals/{id}               # 수정 (waiting/in_progress만)
DELETE /api/v2/proposals/{id}               # 삭제 (waiting만)
```

#### 2. PM/PL 할당
```
POST   /api/v2/proposals/{id}/assign-pm     # PM 할당
POST   /api/v2/proposals/{id}/assign-pl     # PL 할당
```

응답:
```json
{
  "data": {
    "proposalId": "uuid",
    "projectManagerId": "uuid-pm",
    "projectLeaderId": "uuid-pl",
    "canStart": true,  // PM+PL 모두 할당되면 true
    "message": "PM과 PL이 모두 할당되었습니다. 이제 착수할 수 있습니다."
  }
}
```

#### 3. 상태 전환 (비즈니스 라이프사이클)
```
POST   /api/v2/proposals/{id}/start         # 착수 (waiting→in_progress)
POST   /api/v2/proposals/{id}/complete      # 완료 (in_progress→completed)
POST   /api/v2/proposals/{id}/submit        # 제출 (completed→submitted)
POST   /api/v2/proposals/{id}/close         # 종료 (presentation→closed)
```

**중요**: 기존 `/api/proposals/{id}/start`는 LangGraph 워크플로우 실행. 새로운 `/api/v2/proposals/{id}/start`는 비즈니스 라이프사이클 상태 변경. 서로 다른 역할.

#### 4. 진행률
```
GET    /api/v2/proposals/{id}/progress      # 진행률 조회
```

#### 5. 평가
```
POST   /api/v2/proposals/{id}/evaluation    # 평가 결과 등록
GET    /api/v2/proposals/{id}/evaluations   # 평가 이력 조회
```

#### 6. 생애주기 이벤트
```
GET    /api/v2/proposals/{id}/timeline      # 타임라인 조회
```

#### 7. 아카이브
```
GET    /api/v2/proposals?isArchived=true    # 보관함 조회
```

### v1 Endpoints (기존, 유지)

```
POST   /api/proposals/from-rfp              # RFP 파일 업로드 (LangGraph 시작)
POST   /api/proposals/from-bid              # 공고 ID 입력 (LangGraph 시작)
GET    /api/proposals                       # 목록 (기존 조회)
GET    /api/proposals/{id}                  # 단건 (기존 raw)
POST   /api/proposals/{id}/start            # LangGraph workflow 실행 (기존)
POST   /api/proposals/{id}/resume           # Human review resume (기존)
GET    /api/proposals/{id}/stream           # SSE streaming (기존)
GET    /api/proposals/{id}/history          # Checkpoint history (기존)
POST   /api/proposals/{id}/goto/{step}      # Time-travel (기존)
```

**호환성**: v1은 기존 그대로 유지. 클라이언트가 v2로 마이그레이션하는 동안 병행.

---

## 📊 응답 포맷

### v2 성공 응답
```json
{
  "data": {
    "proposalId": "uuid",
    "projectName": "K공사 터널",
    "status": "in_progress",
    "lifecycleStatus": "in_progress",
    "progressPercentage": 55,
    "phase": 3,
    "projectManagerName": "박준호",
    "projectLeaderName": "최민지",
    "bidPrice": 2300000000,
    "deadlineDate": "2026-03-25",
    "daysRemaining": 5
  },
  "meta": {
    "timestamp": "2026-03-29T14:30:00Z"
  }
}
```

### v2 목록 응답
```json
{
  "data": [
    { /* 제안 객체 */ }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5,
    "hasNextPage": true
  },
  "meta": {
    "timestamp": "2026-03-29T14:30:00Z"
  }
}
```

### v2 에러 응답
```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "현재 상태에서 이 작업을 수행할 수 없습니다",
    "details": [
      { "field": "lifecycleStatus", "message": "진행 중(in_progress) 상태에서만 완료할 수 있습니다" }
    ]
  }
}
```

### v1과의 차이
- v1: raw DB 컬럼명 (`title`, `owner_id`, `status` 워크플로우값)
- v2: 의미 있는 필드명 (`projectName`, `createdBy`, `lifecycleStatus` 비즈니스값)

---

## 🔐 권한 제어

| Endpoint | PM | PL | Team Lead | Executive |
|----------|:--:|:--:|:---------:|:---------:|
| GET /v2/proposals | ✅ | ✅ | ✅ | ✅ |
| POST /v2/proposals | ✅ | ✗ | ✅ | ✅ |
| PUT /v2/proposals | ✅ | ✗ | ✅ | ✅ |
| DELETE /v2/proposals | ✅ | ✗ | ✅ | ✅ |
| assign-pm | ✅ | ✗ | ✅ | ✅ |
| assign-pl | ✅ | ✗ | ✅ | ✅ |
| /start | ✅ | ✅ | ✗ | ✅ |
| /complete | ✅ | ✅ | ✗ | ✅ |
| /submit | ✅ | ✗ | ✅ | ✅ |
| /close | ✅ | ✗ | ✅ | ✅ |

**구현**: `require_role()` 또는 `require_proposal_access()` 미들웨어 사용

---

## 📝 마이그레이션 체크리스트

### Phase 1: Database (1주)
- [ ] `ALTER TABLE proposals ADD lifecycle_status, project_manager_id, project_leader_id, started_at, completed_at, submitted_at, closed_at` 마이그레이션 생성
- [ ] `proposal_timelines` 테이블 생성
- [ ] `proposal_evaluations` 테이블 생성
- [ ] 인덱스 추가 (`lifecycle_status`, `project_manager_id`, `archived_at`)
- [ ] 기존 데이터 마이그레이션 (상태 매핑)

### Phase 2: API (2주)
- [ ] v2 라우터 생성 (`app/api/routes_proposal_v2.py`)
- [ ] CRUD 엔드포인트 구현
- [ ] PM/PL 할당 엔드포인트
- [ ] 상태 전환 엔드포인트 (5개)
- [ ] 진행률, 평가, 타임라인 엔드포인트
- [ ] 에러 처리 및 검증

### Phase 3: Automation (1주)
- [ ] 생애주기 이벤트 기록 로직 (TimelineService)
- [ ] PM+PL 할당 시 자동 상태 신호 로직
- [ ] 진행률 자동 계산 로직 (섹션 기반)
- [ ] 30일 자동 archive 스케줄러 (APScheduler)

### Phase 4: Frontend (2주)
- [ ] v2 API 호출 로직 추가
- [ ] 제안 카드 UI 업데이트 (lifecycle_status 표시)
- [ ] 상태 전환 버튼 추가
- [ ] PM/PL 할당 UI
- [ ] 타임라인 페이지 추가

### Phase 5: Testing (1주)
- [ ] Unit tests (상태 전환 로직)
- [ ] Integration tests (API 엔드포인트)
- [ ] E2E tests (전체 워크플로우)
- [ ] Zero Script QA (로그 검증)

---

## 🚀 롤아웃 전략

### 초기 (1주)
1. DB 마이그레이션 배포
2. v2 API 배포 (기능 플래그 `USE_LIFECYCLE_V2=false`)
3. 내부 테스트

### 중기 (2주)
1. 기능 플래그 활성화 (`USE_LIFECYCLE_V2=true`)
2. 프론트엔드 부분 마이그레이션 (기존 화면 유지, v2 API 호출)
3. 사용자 피드백 수집

### 후기 (4주)
1. v1 엔드포인트 deprecated 공지
2. v1 엔드포인트 제거 (또는 리다이렉트)
3. v1 라우터 정리

---

## ✅ 주요 이슈 해결

### 1. 상태 충돌
**문제**: 기존 16개 워크플로우 상태 vs 신규 6개 비즈니스 상태
**해결**: 이중 모델 (lifecycle_status + status)

### 2. /start 엔드포인트 충돌
**문제**: 기존 `/api/proposals/{id}/start` = LangGraph 실행
**해결**: v2에서는 `/api/v2/proposals/{id}/start` 상태 전환 (다른 의미)

### 3. PM/PL 필드 부재
**문제**: 기존 proposals에 PM/PL 필드 없음
**해결**: 마이그레이션으로 신규 컬럼 추가

### 4. Timeline 부재
**문제**: 기존 상태 전환 이벤트 추적 안 함
**해결**: proposal_timelines 테이블 신규 생성

### 5. API 응답 포맷 차이
**문제**: v1은 raw snake_case, v2는 camelCase 기대
**해결**: Pydantic response model with `alias_generator = to_camel` (v2만)

---

## 📌 구현 순서 (우선순위)

### P0 - Critical (1주)
1. Database migration (lifecycle_status, PM/PL 컬럼)
2. v2 기본 CRUD (GET/POST)
3. 상태 전환 엔드포인트 (/start, /complete, /submit)

### P1 - Important (1주)
4. PM/PL 할당 엔드포인트
5. 진행률 조회
6. 타임라인 조회

### P2 - Nice-to-have (1주)
7. 평가 이력
8. Archive 관리
9. 자동 30일 archive 스케줄러

---

## 참고: 기존 구현 보존 목록

다음은 **절대로 제거하면 안 되는** 기존 기능:

- ✅ LangGraph 40개 노드 워크플로우 (유지)
- ✅ RFP 업로드/분석 (`from-rfp` 엔드포인트)
- ✅ G2B 공고 검색/입찰 (`from-bid` 엔드포인트)
- ✅ 섹션 병렬/순차 작성 (proposal_write_next 노드)
- ✅ 자가진단 4개축 점수 (self_review 노드)
- ✅ 다중 스트림 워크플로우 (submission_docs, bidding_stream)
- ✅ 입찰 관리 (bid_confirmed_*, bid_submitted_* 컬럼)
- ✅ Compliance Matrix 추적
- ✅ HWPX/DOCX 산출물 빌드

