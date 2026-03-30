# Phase 1: 제안 프로젝트 상태 시스템 - 스키마 및 용어 정의

## 📚 용어집 (Glossary)

### 비즈니스 용어 (Business Terms)

| 용어 | 영문 | 정의 | 글로벌 표준 매핑 |
|------|------|------|-----------------|
| 제안 프로젝트 | Proposal Project | 용역과제 입찰을 위한 제안서 작성 프로젝트 | Project, Task |
| 발주기관 | Client / Procuring Entity | 용역과제를 발주하는 정부 기관 또는 공공기관 | Organization, Client |
| 제안팀 | Proposal Team | 해당 제안 프로젝트를 담당하는 조직 내 팀 | Team, Department |
| PM | Project Manager | 제안 프로젝트의 전체 책임자 | Project Manager, Lead |
| PL | Project Leader | 제안 작성의 기술적 리더 | Technical Lead, Owner |
| 마감일 | Deadline | 발주기관에 제안서를 제출해야 하는 마지막 날짜 | Deadline, Due Date |
| 입찰가 | Bid Price | 제안에서 제시하는 예정가격 또는 최종 입찰가 | Bid Amount, Quotation |
| D-day | Days Remaining | 마감일까지 남은 일수 (D-0 = 마감당일) | Time To Deadline |
| 제안서 | Proposal Document | 작성되는 최종 제안 문서 (DOCX/HWPX 형식) | Document, Deliverable |
| 섹션 | Section | 제안서의 구성 단위 (예: 기술방안, 가격, 관리계획 등) | Chapter, Part |
| 자가진단 | Self-Assessment | AI가 제안서의 품질을 4개축 100점으로 평가 | Quality Score, Evaluation |
| 컴플라이언스 매트릭스 | Compliance Matrix | 발주기관 요구사항 vs 제안서 내용 매핑 | Requirements Traceability |
| 발표자료 | Presentation Material | 최종 발표 시 사용하는 PPT/자료 | Presentation Deck, Slides |
| 리허설 | Rehearsal | 실제 발표 전 사내 모의 발표 | Mock Presentation, Dry Run |
| 평가결과 | Evaluation Result | 발주기관의 평가 후 수주/탈락 여부 | Award Decision, Outcome |
| 교훈 | Lesson Learned | 프로젝트 종료 후 다음 제안에 활용할 개선사항 | Lesson, Insight |

### 글로벌 표준

| 용어 | 정의 | 참조 |
|------|------|------|
| UUID | 범용 고유 식별자 | RFC 4122 |
| Timestamp | ISO 8601 형식의 시간 기록 | 2026-03-29T14:30:00Z |
| Status Enum | 정의된 상태값 중 하나 | WAITING, IN_PROGRESS, ... |
| Percentage | 0~100 범위의 진행률 | 0%, 50%, 100% |
| Currency | ISO 4217 통화 코드 + 금액 | KRW 2,500,000,000 |
| REST API | 표준 HTTP 메서드 기반 API | GET, POST, PUT, DELETE |

### 용어 매핑

| 비즈니스 용어 | ↔ | 코드 용어 | API 응답명 |
|---|---|---|---|
| 제안 프로젝트 | ↔ | proposal | Proposal |
| 발주기관 | ↔ | client | clientName |
| 제안팀 | ↔ | team | teamName |
| PM | ↔ | project_manager | projectManagerName |
| PL | ↔ | project_leader | projectLeaderName |
| 마감일 | ↔ | deadline | deadlineDate |
| 입찰가 | ↔ | bid_price | bidPrice |
| 상태 | ↔ | status | status |
| 진행률 | ↔ | progress_percentage | progressPercentage |
| 평가결과 | ↔ | evaluation_result | evaluationResult |

---

## 🏗️ 엔티티 정의 (Entities)

### 1. Proposal (제안 프로젝트)

**용도**: 제안 프로젝트의 전체 생애주기 관리

**핵심 속성**:
- **프로젝트 식별**: id, project_code
- **기본 정보**: project_name, client_name, description
- **팀 정보**: team_id, project_manager_id, project_leader_id
- **재정 정보**: bid_price, planned_budget, estimated_cost
- **일정 정보**: deadline_date, started_at, completed_at, submitted_at, closed_at
- **상태 관리**: status, progress_percentage, phase
- **문서 정보**: proposal_document_url, presentation_material_url
- **평가 정보**: evaluation_result, evaluation_score, is_awarded
- **아카이브**: is_archived, archived_at

```sql
CREATE TABLE proposals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_code VARCHAR(50) UNIQUE NOT NULL,
  project_name VARCHAR(255) NOT NULL,
  client_name VARCHAR(255) NOT NULL,
  description TEXT,

  -- Team Assignment
  team_id UUID NOT NULL REFERENCES teams(id),
  project_manager_id UUID REFERENCES users(id),
  project_leader_id UUID REFERENCES users(id),

  -- Financial
  bid_price DECIMAL(15, 2),
  planned_budget DECIMAL(15, 2),
  estimated_cost DECIMAL(15, 2),

  -- Timeline
  deadline_date DATE NOT NULL,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  submitted_at TIMESTAMP,
  closed_at TIMESTAMP,
  archived_at TIMESTAMP,

  -- Status & Progress
  status VARCHAR(50) NOT NULL DEFAULT 'waiting',
    -- ENUM: waiting, in_progress, completed, submitted, presentation, closed, archived
  progress_percentage INT DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
  phase INT DEFAULT 0 CHECK (phase >= 0 AND phase <= 5),

  -- Document References
  proposal_document_url VARCHAR(500),
  presentation_material_url VARCHAR(500),
  compliance_matrix_url VARCHAR(500),

  -- Evaluation
  evaluation_result VARCHAR(50),
    -- ENUM: awaiting, qualified, shortlisted, awarded, rejected, disqualified
  evaluation_score INT,
  is_awarded BOOLEAN DEFAULT FALSE,

  -- Archive
  is_archived BOOLEAN DEFAULT FALSE,

  -- Audit
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by UUID REFERENCES users(id),

  CONSTRAINT valid_dates CHECK (
    (started_at IS NULL OR started_at >= created_at) AND
    (completed_at IS NULL OR completed_at >= started_at) AND
    (submitted_at IS NULL OR submitted_at >= completed_at) AND
    (closed_at IS NULL OR closed_at >= submitted_at) AND
    (archived_at IS NULL OR archived_at > closed_at)
  )
);
```

### 2. ProposalStatus (상태 정의)

**용도**: 제안 프로젝트의 상태 및 전환 규칙 정의

```python
class ProposalStatus(str, Enum):
    WAITING = "waiting"              # 대기: PM/PL 할당 완료, 착수 대기
    IN_PROGRESS = "in_progress"      # 진행: 제안서 작성 중
    COMPLETED = "completed"          # 완료: 작성 완료, 최종 검토 중
    SUBMITTED = "submitted"          # 제출: 제출 후 평가 대기
    PRESENTATION = "presentation"    # 발표: 발표 준비 및 리허설
    CLOSED = "closed"                # 종료: 평가 결과 등록 및 피드백 정리
    ARCHIVED = "archived"            # 보관: 종료 후 30일 자동 이동
```

### 3. ProposalPhase (진행 단계)

**용도**: 제안서 작성의 5단계 진행도 추적

```python
class ProposalPhase(IntEnum):
    PHASE_0 = 0  # 대기
    PHASE_1 = 1  # RFP 분석 및 기획
    PHASE_2 = 2  # 전략 수립
    PHASE_3 = 3  # 팀 구성 및 일정 계획
    PHASE_4 = 4  # 제안서 본문 작성
    PHASE_5 = 5  # 최종 검토 및 제출 준비
```

### 4. ProposalTimeline (생애주기 이벤트)

**용도**: 제안 프로젝트의 주요 전환 시점 기록

```sql
CREATE TABLE proposal_timelines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  event_type VARCHAR(50) NOT NULL,
    -- ENUM: created, assigned, started, phase_completed, reviewed, submitted, evaluation_started,
    --       awarded/rejected, closed, archived
  event_description TEXT,

  previous_status VARCHAR(50),
  new_status VARCHAR(50) NOT NULL,
  triggered_by UUID NOT NULL REFERENCES users(id),
  triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  metadata JSONB,  -- 추가 정보 (예: 평가 점수, 탈락 사유 등)

  FOREIGN KEY (proposal_id) REFERENCES proposals(id)
);
```

### 5. ProposalTeamMember (팀 멤버)

**용도**: 제안 프로젝트에 참여하는 팀원 관리

```sql
CREATE TABLE proposal_team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),

  role VARCHAR(50) NOT NULL,
    -- ENUM: project_manager, project_leader, technical_writer, designer, qa
  contribution_area VARCHAR(255),  -- 담당 영역

  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  left_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,

  UNIQUE(proposal_id, user_id, role)
);
```

### 6. ProposalSection (제안서 섹션)

**용도**: 제안서의 개별 섹션 관리

```sql
CREATE TABLE proposal_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  section_name VARCHAR(100) NOT NULL,
  section_type VARCHAR(50) NOT NULL,
    -- ENUM: executive_summary, technical_approach, organization, schedule, pricing, maintenance, ...
  section_number INT,  -- 순서

  content_url VARCHAR(500),  -- 섹션 문서 경로
  estimated_pages INT,

  status VARCHAR(50) DEFAULT 'pending',
    -- ENUM: pending, in_draft, in_review, approved
  assigned_to UUID REFERENCES users(id),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,

  UNIQUE(proposal_id, section_name)
);
```

### 7. ProposalEvaluation (평가 정보)

**용도**: 발주기관의 평가 결과 기록

```sql
CREATE TABLE proposal_evaluations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  evaluation_date DATE,
  evaluation_type VARCHAR(50),
    -- ENUM: documentary_review, presentation, interview, technical_review

  -- 4개축 자가진단 (AI 평가)
  self_assessment_score INT,  -- 0~100
  technical_score INT,
  organizational_score INT,
  commercial_score INT,

  -- 최종 평가 (발주기관)
  client_evaluation_score INT,  -- 0~100 또는 합격/불합격
  evaluation_result VARCHAR(50),
    -- ENUM: pending, qualified, shortlisted, awarded, rejected
  rejection_reason TEXT,

  evaluated_at TIMESTAMP,
  evaluated_by VARCHAR(255),  -- 평가자 정보

  notes JSONB,  -- 추가 평가 의견

  UNIQUE(proposal_id, evaluation_type)
);
```

### 8. ProposalLessonLearned (교훈 기록)

**용도**: 프로젝트 종료 후 개선사항 및 교훈 정리

```sql
CREATE TABLE proposal_lessons_learned (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

  lesson_category VARCHAR(50) NOT NULL,
    -- ENUM: technical, organizational, commercial, client_interaction, market

  lesson_description TEXT NOT NULL,
  lesson_impact VARCHAR(50),
    -- ENUM: high, medium, low

  applicable_to_future BOOLEAN DEFAULT TRUE,

  recorded_by UUID NOT NULL REFERENCES users(id),
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  kb_linked BOOLEAN DEFAULT FALSE,  -- KB에 연동되었는지 여부
  kb_url VARCHAR(500)
);
```

---

## 🔗 관계도 (Relationships)

```
┌─────────────────────────────────────────────────────────┐
│                    Proposal (제안)                       │
│  id, project_code, project_name, client_name, status   │
└──────────────────┬──────────────────────────────────────┘
                   │ 1:1
                   ├──→ Team (팀)
                   ├──→ User (PM)
                   ├──→ User (PL)
                   │
                   │ 1:N
                   ├──→ ProposalTimeline (생애주기 이벤트)
                   ├──→ ProposalTeamMember (팀원)
                   ├──→ ProposalSection (섹션)
                   ├──→ ProposalEvaluation (평가)
                   └──→ ProposalLessonLearned (교훈)
```

**관계 설명**:

| 관계 | 설명 | Cardinality |
|------|------|------------|
| Proposal ↔ Team | 한 제안은 하나의 팀에 속함 | 1:N |
| Proposal ↔ User (PM) | 한 제안은 하나의 PM을 가짐 | 1:1 |
| Proposal ↔ User (PL) | 한 제안은 하나의 PL을 가짐 | 1:1 |
| Proposal ↔ ProposalSection | 한 제안은 여러 섹션으로 구성 | 1:N |
| Proposal ↔ ProposalTimeline | 한 제안은 여러 생애주기 이벤트를 가짐 | 1:N |
| ProposalSection ↔ User | 섹션은 담당자에게 할당 | N:1 |

---

## 📊 데이터 흐름 (Data Flow)

```
1. 신규 제안 생성
   → Proposal (status=waiting)
   → ProposalTimeline (event=created)

2. PM/PL 할당
   → Proposal.project_manager_id, project_leader_id 업데이트
   → ProposalTimeline (event=assigned)

3. 착수 (상태 전환: waiting → in_progress)
   → Proposal.status = 'in_progress'
   → Proposal.started_at = NOW()
   → ProposalTimeline (event=started)

4. 섹션별 작성
   → ProposalSection (status=in_draft) 업데이트
   → 각 섹션 완료 시 (status=approved)

5. 최종 검토 (상태 전환: in_progress → completed)
   → ProposalEvaluation.self_assessment_score 기록
   → ProposalTimeline (event=phase_completed)

6. 제출 (상태 전환: completed → submitted)
   → Proposal.status = 'submitted'
   → Proposal.submitted_at = NOW()
   → Proposal.proposal_document_url 저장
   → ProposalTimeline (event=submitted)

7. 발표 (상태 전환: submitted → presentation)
   → Proposal.status = 'presentation'
   → Proposal.presentation_material_url 저장
   → ProposalTimeline (event=presentation_started)

8. 종료 (상태 전환: presentation → closed)
   → Proposal.status = 'closed'
   → Proposal.closed_at = NOW()
   → ProposalEvaluation.evaluation_result 기록
   → ProposalLessonLearned 입력
   → ProposalTimeline (event=closed)

9. 자동 아카이브 (30일 후)
   → Proposal.status = 'archived'
   → Proposal.archived_at = NOW()
   → Proposal.is_archived = TRUE
   → ProposalTimeline (event=archived)
```

---

## 🔐 데이터 무결성 제약 (Constraints)

### 1. 상태 전환 규칙

```sql
-- 유효한 상태 전환만 허용
WAITING → IN_PROGRESS (착수 버튼 클릭)
IN_PROGRESS → COMPLETED (모든 섹션 완료)
COMPLETED → SUBMITTED (제출 버튼 클릭)
SUBMITTED → PRESENTATION (평가대상 확정) OR CLOSED (탈락)
PRESENTATION → CLOSED (발표 완료)
CLOSED → ARCHIVED (30일 경과, 자동)
```

### 2. 날짜 순서 검증

```sql
created_at < started_at < completed_at < submitted_at < archived_at
```

### 3. PM/PL 필수 조건

```sql
status = IN_PROGRESS 일 때:
  project_manager_id NOT NULL AND
  project_leader_id NOT NULL
```

### 4. 진행률 자동 계산

```
progress_percentage = (완료된 섹션 수 / 전체 섹션 수) * 100

PHASE 0: 0%    (대기)
PHASE 1: 20%   (RFP 분석 완료)
PHASE 2: 40%   (전략 수립 완료)
PHASE 3: 60%   (팀 구성 완료)
PHASE 4: 80%   (본문 작성 완료)
PHASE 5: 100%  (최종 검토 완료)
```

---

## 📋 용어 사용 규칙 (Usage Rules)

### 코드에서:
```python
# 스네이크 케이스
project_manager_id
project_leader_id
bid_price
proposal_document_url
is_archived
```

### API 응답에서:
```json
{
  "proposalId": "uuid",
  "projectName": "K공사 터널 운영",
  "clientName": "K공사",
  "projectManagerName": "박준호",
  "projectLeaderName": "최민지",
  "status": "in_progress",
  "progressPercentage": 55,
  "bidPrice": 2300000000,
  "deadlineDate": "2026-03-25",
  "evaluationResult": "pending"
}
```

### 사용자 인터페이스에서:
```
한글 표시
제안 프로젝트 | K공사 터널 운영 용역
발주기관: K공사
제안팀: 수주전략팀
PM: 박준호
PL: 최민지
상태: 진행 중
진행률: 55%
```

---

## ✅ Phase 1 체크리스트

- [x] 비즈니스 용어 정의 (10개 주요 용어)
- [x] 글로벌 표준 매핑 (6개 표준)
- [x] 주요 엔티티 정의 (8개 엔티티)
- [x] 데이터베이스 스키마 (SQL DDL)
- [x] 엔티티 관계도 작성
- [x] 데이터 흐름 정의
- [x] 데이터 무결성 제약 정의
- [x] 용어 사용 규칙 수립

---

## 📌 다음 단계

**Phase 2**: 코딩 컨벤션 정의 (naming, structure, patterns)
→ `docs/01-plan/coding-conventions.md`

**Phase 3**: API 스키마 및 엔드포인트 설계
→ Phase 4에서 상세 설계

