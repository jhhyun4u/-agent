# 통합 상태 시스템 구현 계획
## (기존 16개 + 신규 6개 → 10개 Business Status)

> **작성일**: 2026-03-29
> **마이그레이션 기간**: 3-4일
> **설계 문서**: `docs/02-design/proposal-integrated-workflow-v5.0.md`
> **상태**: 계획 수립 완료

---

## 📋 개요

### 목표
기존 16개 분산된 상태값을 10개의 비즈니스 상태로 통합하고, 3-레이어 구조로 세밀한 워크플로우 제어와 높은 수준의 생애주기 추적을 동시에 지원한다.

### 3-레이어 아키텍처
1. **Layer 1 (Business Status)**: proposals.status (10개) — 사용자/PM이 보는 높은 수준의 단계
2. **Layer 2 (Workflow Phase)**: proposals.current_phase (text) — LangGraph 40개 노드가 관리하는 세밀한 진행도
3. **Layer 3 (AI Runtime)**: ai_task_status 테이블 — 임시 실행 상태 (running, paused, error, no_response)

### 핵심 변화
| 영역 | 기존 | 신규 |
|------|------|------|
| Status 값 | 16개 (상태 산재) | **10개** (통합) + win_result (세부) |
| DB 제약 | CHECK constraint에서 모순 | 전체 재정의 |
| 타임스탐프 | 생성/수정만 | **8개** (단계별 이벤트) |
| 추적 테이블 | 없음 | proposal_timelines (이벤트 로그) |
| AI 상태 | status에 혼입 (running, failed) | **ai_task_status 분리** |

---

## 🚨 **Phase 0: CRITICAL BUG FIX** (1일)

### Issue
```
routes_workflow.py:153 → status = "running"
routes_workflow.py:298 → status = "cancelled"
database/schema_v3.4.sql:117 → CHECK constraint에 없음
→ PostgreSQL UPDATE 거부 → 500 Internal Error
```

### 해결 방법
1. **즉시 핫픽스**: Layer 3 분리 전까지 임시로 CHECK constraint 확장
   ```sql
   ALTER TABLE proposals DROP CONSTRAINT status_check;
   ALTER TABLE proposals ADD CONSTRAINT status_check
     CHECK (status IN (
       'waiting','in_progress','completed','submitted',
       'presentation','closed','archived','on_hold','expired',
       'running','cancelled','paused','failed'  -- 임시 허용
     ));
   ```

2. **routes_workflow.py 수정**: status 저장 로직을 ai_task_status로 전환 (Phase 2에서)

### 성공 기준
- [ ] 라이브 환경에서 제안서 워크플로우 500 에러 해결
- [ ] 로컬/스테이징에서 제안서 시작~완료 전체 플로우 테스트 통과

---

## **Phase 1: 데이터베이스 마이그레이션** (1일)

### 목표
- proposals 테이블에 신규 컬럼 추가
- proposal_timelines, ai_task_status 신규 테이블 생성
- 기존 16개 상태값 → 10개 새 상태값 마이그레이션
- CHECK constraint 정의 완료

### 구성 파일
**신규 파일**: `database/migrations/018_status_unification.sql`

### 1.1 신규 컬럼 추가 (proposals 테이블)

```sql
-- Layer 1: Business Status (10개) + win_result (세부)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS
  status VARCHAR(50) NOT NULL DEFAULT 'waiting';

ALTER TABLE proposals ADD COLUMN IF NOT EXISTS
  win_result VARCHAR(50);

-- Layer 2: Workflow Phase
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS
  current_phase TEXT;

-- Layer 1: 단계별 타임스탐프
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS presentation_started_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS expired_at TIMESTAMP;

-- 담당자 할당
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS project_manager_id UUID;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS project_leader_id UUID;
```

### 1.2 신규 테이블 생성

#### A. proposal_timelines (이벤트 추적)
```sql
CREATE TABLE proposal_timelines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  event_type VARCHAR(50) NOT NULL,  -- status_change, phase_change, review_comment, etc.
  from_status VARCHAR(50),
  to_status VARCHAR(50),
  from_phase TEXT,
  to_phase TEXT,

  triggered_by VARCHAR(50),  -- user, system, cron
  triggered_by_user_id UUID,

  event_data JSONB,  -- 메타데이터 (win_result, reason, etc.)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT timeline_event_check CHECK (event_type IN (
    'status_change', 'phase_change', 'review_comment',
    'ai_complete', 'archive', 'expire', 'hold', 'release'
  ))
);

CREATE INDEX idx_proposal_timelines_proposal_id ON proposal_timelines(proposal_id);
CREATE INDEX idx_proposal_timelines_event_type ON proposal_timelines(event_type);
CREATE INDEX idx_proposal_timelines_created_at ON proposal_timelines(created_at DESC);
```

#### B. ai_task_status (Layer 3: 임시 실행 상태)
```sql
CREATE TABLE ai_task_status (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  status VARCHAR(50) NOT NULL,  -- running, paused, error, no_response, complete
  current_node TEXT,
  error_message TEXT,

  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_heartbeat TIMESTAMP,
  ended_at TIMESTAMP,

  session_id TEXT,  -- LangGraph 세션 ID

  CONSTRAINT ai_status_check CHECK (status IN (
    'running', 'paused', 'error', 'no_response', 'complete'
  )),

  CONSTRAINT active_ai_status UNIQUE (proposal_id)
    WHERE status IN ('running', 'paused')  -- 한 번에 하나만 활성
);

CREATE INDEX idx_ai_task_status_proposal_id ON ai_task_status(proposal_id);
CREATE INDEX idx_ai_task_status_status ON ai_task_status(status);
```

### 1.3 기존 상태값 마이그레이션

#### 마이그레이션 로직 (SQL + Python)

**SQL 부분**:
```sql
BEGIN;

-- Step 1: 기존 'status' 컬럼 백업 (임시명)
ALTER TABLE proposals RENAME COLUMN status TO status_old;

-- Step 2: 새 status 컬럼 추가 (기본값 'waiting')
ALTER TABLE proposals ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'waiting';

-- Step 3: 매핑 데이터 마이그레이션 (UPDATE 또는 Python)
-- 아래 Python 스크립트로 수행

-- Step 4: 기존 컬럼 삭제
ALTER TABLE proposals DROP COLUMN status_old;

-- Step 5: 제약 조건 추가
ALTER TABLE proposals ADD CONSTRAINT status_check CHECK (
  status IN ('waiting','in_progress','completed','submitted',
             'presentation','closed','archived','on_hold','expired')
);

ALTER TABLE proposals ADD CONSTRAINT win_result_check CHECK (
  win_result IS NULL OR
  win_result IN ('won','lost','no_go','abandoned','cancelled')
);

COMMIT;
```

**Python 부분** (`scripts/migrate_states_018.py`):
```python
# 마이그레이션 매핑 테이블
STATE_MAPPING = {
    'initialized': ('waiting', None),
    'processing': ('in_progress', None),
    'searching': ('in_progress', None),
    'analyzing': ('in_progress', None),
    'strategizing': ('in_progress', None),
    'completed': ('completed', None),
    'submitted': ('submitted', None),
    'presented': ('presentation', None),
    'won': ('closed', 'won'),
    'lost': ('closed', 'lost'),
    'no_go': ('closed', 'no_go'),
    'abandoned': ('closed', 'abandoned'),
    'retrospect': ('closed', None),  # 교훈 기록은 proposal_timelines에서 추적
    'on_hold': ('on_hold', None),
    'expired': ('expired', None),
    'running': ('in_progress', None),  # AI 상태 → ai_task_status로 분리
    'failed': ('in_progress', None),
    'cancelled': ('closed', 'cancelled'),
    'paused': ('in_progress', None),
}

# 각 proposal에 대해:
# 1. 기존 status → 새 status, win_result 매핑
# 2. status가 'closed'인 경우 closed_at = now()
# 3. status가 'archived'인 경우 archived_at = now()
# 4. proposal_timelines 레코드 생성 (현재 상태 스냅샷)
```

### 1.4 CHECK 제약 최종 정의
```sql
-- 모든 단계 후 최종 제약 확인
ALTER TABLE proposals ADD CONSTRAINT status_final_check CHECK (
  status IN ('waiting','in_progress','completed','submitted',
             'presentation','closed','archived','on_hold','expired')
),
ADD CONSTRAINT win_result_final_check CHECK (
  (status = 'closed') OR (win_result IS NULL)  -- win_result는 closed일 때만 의미
);
```

### 성공 기준
- [ ] 마이그레이션 스크립트 실행 후 모든 proposal 상태가 올바르게 변환됨
- [ ] proposal_timelines 초기 레코드 생성됨
- [ ] ai_task_status 테이블 생성되고 기존 'running' 상태 proposal 이관됨
- [ ] 데이터 무결성 체크 통과
  ```sql
  SELECT COUNT(*) FROM proposals WHERE status NOT IN ('...');  -- 0
  SELECT COUNT(*) FROM proposals WHERE status='closed' AND win_result IS NULL;  -- 0
  ```

---

## **Phase 2: 백엔드 코드 구현** (1일)

### 목표
- ProposalStatus, WinResult Enum 정의
- routes_workflow.py에서 ai_task_status 분리
- TimelineService 구현 (이벤트 추적)
- 상태 전환 로직 통합
- 기존 상태 기반 코드 업데이트

### 2.1 Enum 정의

**파일**: `app/models/types.py` (신규) 또는 `app/models/schemas.py` (기존 확장)

```python
from enum import Enum

class ProposalStatus(str, Enum):
    WAITING       = "waiting"
    IN_PROGRESS   = "in_progress"
    COMPLETED     = "completed"
    SUBMITTED     = "submitted"
    PRESENTATION  = "presentation"
    CLOSED        = "closed"
    ARCHIVED      = "archived"
    ON_HOLD       = "on_hold"
    EXPIRED       = "expired"

class WinResult(str, Enum):
    WON        = "won"
    LOST       = "lost"
    NO_GO      = "no_go"
    ABANDONED  = "abandoned"
    CANCELLED  = "cancelled"

class AITaskStatus(str, Enum):
    RUNNING     = "running"
    PAUSED      = "paused"
    ERROR       = "error"
    NO_RESPONSE = "no_response"
    COMPLETE    = "complete"
```

### 2.2 TimelineService 구현

**파일**: `app/services/timeline_service.py` (신규)

```python
class TimelineService:
    async def record_status_change(
        self,
        proposal_id: UUID,
        from_status: str,
        to_status: str,
        win_result: Optional[str] = None,
        triggered_by_user_id: Optional[UUID] = None,
    ) -> None:
        """상태 변경 이벤트 기록"""

    async def record_phase_change(
        self,
        proposal_id: UUID,
        from_phase: str,
        to_phase: str,
        triggered_by_user_id: Optional[UUID] = None,
    ) -> None:
        """LangGraph 위상 변경 이벤트 기록"""

    async def record_review_comment(
        self,
        proposal_id: UUID,
        comment: str,
        section: Optional[str] = None,
        triggered_by_user_id: Optional[UUID] = None,
    ) -> None:
        """리뷰 코멘트 기록"""
```

### 2.3 AI Task Status 분리 (Critical Bug Fix)

**파일**: `app/services/ai_status_manager.py` (확장)

```python
class AIStatusManager:
    async def start_task(
        self,
        proposal_id: UUID,
        session_id: str,
        current_node: str,
    ) -> None:
        """AI 작업 시작 → ai_task_status='running' 기록"""
        # proposals.status는 변경하지 않음 (계속 'in_progress' 유지)

    async def pause_task(self, proposal_id: UUID) -> None:
        """AI 작업 일시중지 → ai_task_status='paused'"""

    async def error_task(
        self,
        proposal_id: UUID,
        error_message: str,
    ) -> None:
        """AI 작업 에러 → ai_task_status='error'"""

    async def complete_task(self, proposal_id: UUID) -> None:
        """AI 작업 완료 → ai_task_status='complete'"""
```

**routes_workflow.py 수정**:
```python
# 기존 (잘못된)
status = "running"  # ❌ proposals.status에 저장 → CHECK constraint 위반

# 신규 (올바른)
ai_status = AITaskStatus.RUNNING
await ai_status_manager.start_task(proposal_id, session_id, "rfp_analyze")
# ✅ ai_task_status 테이블에 저장 → 제약 조건 준수
```

### 2.4 상태 전환 로직 통합

**파일**: `app/services/state_transition_service.py` (신규)

```python
class StateTransitionService:
    async def transition(
        self,
        proposal_id: UUID,
        to_status: ProposalStatus,
        win_result: Optional[WinResult] = None,
        triggered_by_user_id: Optional[UUID] = None,
    ) -> None:
        """상태 전환 with 검증, 타임스탬프 업데이트, 이벤트 기록"""

        # 1. 전환 가능성 검증
        current = await self.get_current_status(proposal_id)
        if not self._is_valid_transition(current, to_status):
            raise InvalidStateTransition(...)

        # 2. 타임스탬프 업데이트
        updates = {}
        if to_status == ProposalStatus.IN_PROGRESS:
            updates['started_at'] = datetime.now(timezone.utc)
        elif to_status == ProposalStatus.COMPLETED:
            updates['completed_at'] = datetime.now(timezone.utc)
        elif to_status == ProposalStatus.SUBMITTED:
            updates['submitted_at'] = datetime.now(timezone.utc)
        elif to_status == ProposalStatus.CLOSED:
            updates['closed_at'] = datetime.now(timezone.utc)
        elif to_status == ProposalStatus.ARCHIVED:
            updates['archived_at'] = datetime.now(timezone.utc)

        # 3. DB 업데이트
        await db.proposals.update(proposal_id, status=to_status, win_result=win_result, **updates)

        # 4. 이벤트 기록
        await timeline_service.record_status_change(
            proposal_id, current, to_status, win_result, triggered_by_user_id
        )
```

### 2.5 기존 코드 업데이트

**검색 대상**:
```bash
grep -r "status.*=.*'processing'" app/
grep -r "status.*=.*'won'" app/
grep -r "status.*=.*'lost'" app/
# ... 등등
```

**업데이트 패턴**:
```python
# 기존
if proposal.status == 'won':
    # ...

# 신규
if proposal.status == ProposalStatus.CLOSED and proposal.win_result == WinResult.WON:
    # ...
```

### 2.6 쿼리 업데이트

**routes_proposal.py**:
```python
# 기존
proposals = await db.proposals.filter(status='in_progress')

# 신규
proposals = await db.proposals.filter(status=ProposalStatus.IN_PROGRESS)
```

### 성공 기준
- [ ] 모든 Enum 타입 정의 완료
- [ ] TimelineService, AIStatusManager, StateTransitionService 구현 완료
- [ ] routes_workflow.py에서 'running'/'cancelled' 상태 저장 제거
- [ ] 모든 proposal 상태 비교가 Enum 사용
- [ ] 단위 테스트 통과 (상태 전환 로직)

---

## **Phase 3: 프론트엔드 업데이트** (0.5일)

### 목표
- TypeScript ProposalStatus 타입 업데이트
- 컴포넌트 props 타입 수정
- 상태 필터/배지 UI 업데이트
- API 응답 타입 동기화

### 3.1 타입 정의 업데이트

**파일**: `frontend/app/types/proposal.ts` (또는 기존 types 파일)

```typescript
// 기존 (16개 문자열)
type ProposalStatus =
  | 'initialized' | 'processing' | 'searching' | 'analyzing' | 'strategizing'
  | 'completed' | 'submitted' | 'presented'
  | 'won' | 'lost' | 'no_go' | 'abandoned' | 'retrospect'
  | 'on_hold' | 'expired'
  | 'running' | 'failed' | 'cancelled' | 'paused';

// 신규 (10개 + win_result)
type ProposalStatus =
  | 'waiting' | 'in_progress' | 'completed' | 'submitted' | 'presentation'
  | 'closed' | 'archived' | 'on_hold' | 'expired';

type WinResult = 'won' | 'lost' | 'no_go' | 'abandoned' | 'cancelled';

interface Proposal {
  // ...
  status: ProposalStatus;
  win_result?: WinResult;  // closed일 때만 의미
  current_phase?: string;  // LangGraph 노드명
  started_at?: Date;
  completed_at?: Date;
  submitted_at?: Date;
  presentation_started_at?: Date;
  closed_at?: Date;
  archived_at?: Date;
  expired_at?: Date;
  project_manager_id?: string;
  project_leader_id?: string;
}
```

### 3.2 상태 배지 컴포넌트 업데이트

**파일**: `frontend/app/components/ProposalStatusBadge.tsx`

```typescript
const STATUS_COLORS: Record<ProposalStatus, string> = {
  'waiting': 'bg-gray-200 text-gray-800',
  'in_progress': 'bg-blue-200 text-blue-800',
  'completed': 'bg-green-200 text-green-800',
  'submitted': 'bg-purple-200 text-purple-800',
  'presentation': 'bg-orange-200 text-orange-800',
  'closed': 'bg-red-200 text-red-800',  // win_result로 세부 표시
  'archived': 'bg-gray-500 text-gray-100',
  'on_hold': 'bg-yellow-200 text-yellow-800',
  'expired': 'bg-red-500 text-white',
};

// win_result 세부 표시
const renderClosedStatus = (winResult?: WinResult) => {
  switch (winResult) {
    case 'won': return '수주';
    case 'lost': return '패찰';
    case 'no_go': return '노고';
    case 'abandoned': return '중단';
    case 'cancelled': return '취소';
    default: return '종료';
  }
};
```

### 3.3 필터 UI 업데이트

**파일**: `frontend/app/components/ProposalListFilters.tsx`

```typescript
const filters = [
  { value: 'waiting', label: '⏳ 대기', color: 'gray' },
  { value: 'in_progress', label: '📝 진행', color: 'blue' },
  { value: 'completed', label: '✅ 완료', color: 'green' },
  { value: 'submitted', label: '📤 제출', color: 'purple' },
  { value: 'presentation', label: '🎤 발표', color: 'orange' },
  { value: 'closed', label: '🏁 종료', color: 'red' },
  { value: 'on_hold', label: '⏸️  보류', color: 'yellow' },
  { value: 'archived', label: '📦 보관', color: 'gray' },
];
```

### 3.4 API 타입 동기화

**파일**: `frontend/app/lib/api.ts` (또는 기존 API 클라이언트)

```typescript
// 기존 getProposals 응답 타입
interface ProposalApiResponse {
  // ...
  status: string;  // 느슨한 타입
}

// 신규
interface ProposalApiResponse {
  // ...
  status: ProposalStatus;  // 엄격한 타입
  win_result?: WinResult;
  started_at?: string;  // ISO 8601
  // ...
}
```

### 성공 기준
- [ ] TypeScript 빌드 에러 0건
- [ ] 프로포절 리스트 페이지 렌더링 정상
- [ ] 상태 배지 색상 올바르게 표시
- [ ] 필터 UI 업데이트 완료

---

## **Phase 4: 테스트 및 검증** (0.5일)

### 목표
- 데이터 무결성 확인
- 전체 워크플로 end-to-end 테스트
- 성능 영향 평가
- 마이그레이션 롤백 계획

### 4.1 데이터 무결성 테스트

**SQL 검증**:
```sql
-- 1. 상태값 검증
SELECT COUNT(*) as invalid_count
FROM proposals
WHERE status NOT IN ('waiting','in_progress','completed','submitted',
                     'presentation','closed','archived','on_hold','expired');
-- 예상: 0

-- 2. win_result 검증
SELECT COUNT(*) as invalid_count
FROM proposals
WHERE (status != 'closed' AND win_result IS NOT NULL)
   OR (status = 'closed' AND win_result IS NULL);
-- 예상: 0

-- 3. 타임스탬프 검증
SELECT COUNT(*) as inconsistent
FROM proposals
WHERE started_at > completed_at
   OR completed_at > submitted_at
   OR submitted_at > closed_at;
-- 예상: 0

-- 4. proposal_timelines 초기 레코드 확인
SELECT COUNT(*) FROM proposal_timelines;
-- 예상: (모든 proposal 수와 동일)

-- 5. ai_task_status 분리 확인
SELECT COUNT(*) FROM ai_task_status WHERE status IN ('running', 'paused');
-- 예상: (기존 running 상태의 proposal 수)
```

### 4.2 End-to-End 테스트

**시나리오**:
1. 새 제안서 생성 → status='waiting'
2. PM/PL 할당 후 착수 → status='in_progress', started_at 기록
3. LangGraph 실행 (Phase 변화 추적) → current_phase 업데이트
4. Go/No-Go 결과 → closed, win_result='no_go'
5. proposal_timelines 이벤트 확인 → 모든 상태 전환이 기록됨

**테스트 코드**:
```python
async def test_proposal_state_lifecycle():
    # 1. 생성
    proposal = await create_proposal(...)
    assert proposal.status == ProposalStatus.WAITING

    # 2. 착수
    await state_transition.transition(
        proposal.id, ProposalStatus.IN_PROGRESS, triggered_by_user_id=user.id
    )
    assert proposal.started_at is not None

    # 3. 완료
    await state_transition.transition(proposal.id, ProposalStatus.COMPLETED)
    assert proposal.completed_at is not None

    # 4. 이벤트 확인
    timelines = await timeline_service.get_timelines(proposal.id)
    assert len(timelines) >= 2
    assert timelines[0].event_type == 'status_change'
```

### 4.3 성능 테스트

**대상**:
- 제안서 리스트 조회 (proposal_timelines 조인 오버헤드)
- 상태 필터링 성능
- ai_task_status 활성 레코드 추적

**기준**:
```
- 제안서 1000개 조회: < 1초
- 상태별 필터링: < 500ms
- ai_task_status 조회: < 100ms
```

### 4.4 롤백 계획

**위험 시나리오**:
- 데이터 마이그레이션 실패
- 백엔드 배포 후 500 에러
- 프론트엔드 타입 에러

**롤백 절차**:
1. **DB 롤백**: `database/migrations/018_status_unification_rollback.sql`
   ```sql
   -- 신규 테이블 삭제
   DROP TABLE IF EXISTS ai_task_status;
   DROP TABLE IF EXISTS proposal_timelines;

   -- 컬럼 삭제
   ALTER TABLE proposals DROP COLUMN IF EXISTS win_result, current_phase, ...;

   -- 기존 status 컬럼 복원
   ALTER TABLE proposals RENAME COLUMN status_new TO status;
   ```

2. **백엔드 롤백**: 이전 버전 배포 (git tag)

3. **프론트엔드 롤백**: 이전 커밋으로 revert

### 성공 기준
- [ ] 데이터 무결성 테스트 100% 통과
- [ ] E2E 테스트 (상태 전환) 통과
- [ ] 성능 테스트 기준 만족
- [ ] 롤백 계획 검증 완료 (dry-run)

---

## 📅 마일스톤 & 일정

| 날짜 | Phase | 작업 | 담당자 | 상태 |
|------|-------|------|--------|------|
| 2026-03-29 | 0 | CRITICAL BUG Fix (CHECK constraint) | - | pending |
| 2026-03-30 | 1 | DB 마이그레이션 + 데이터 마이그레이션 | - | pending |
| 2026-03-31 | 2 | 백엔드 구현 (Enum, Service, Route 업데이트) | - | pending |
| 2026-04-01 | 3 | 프론트엔드 타입 및 UI 업데이트 | - | pending |
| 2026-04-01 오후 | 4 | 테스트, 검증, 라이브 배포 | - | pending |

---

## 🔄 의존성 & 선행 조건

### 선행 조건
- [ ] 설계 문서 (v5.0) 최종 검토 완료
- [ ] 기존 16개 상태값 매핑 테이블 확인
- [ ] DB 마이그레이션 스크립트 (018_status_unification.sql) 작성 완료

### 병렬 처리 불가능
- Phase 0 → Phase 1 (DB 변경 필수)
- Phase 1 → Phase 2 (새 컬럼/테이블 필요)
- Phase 2 → Phase 3 (API 타입 확정 필수)
- Phase 3 → Phase 4 (모든 코드 완성 필요)

---

## ✅ 위험 관리

| 위험 | 영향도 | 대응 방안 |
|------|--------|----------|
| DB 마이그레이션 데이터 손실 | 높음 | 사전 백업 + 롤백 계획 |
| 상태 전환 로직 버그 | 높음 | 단위 테스트 + 수동 테스트 |
| API 응답 타입 불일치 | 중간 | TS 엄격 모드 + 빌드 검증 |
| 성능 저하 (proposal_timelines JOIN) | 낮음 | 인덱스 최적화 + 쿼리 분리 |

---

## 참고 문서

- 설계: `docs/02-design/proposal-integrated-workflow-v5.0.md` (v5.0)
- 기존 상태 분석: `docs/01-plan/proposal-workflow-schema.md` (Phase 1)
- API 스펙: `docs/02-design/proposal-api-spec.md`
