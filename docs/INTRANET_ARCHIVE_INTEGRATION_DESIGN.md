# 인트라넷 자료 + Archive 통합 설계

> **상태:** 통합 설계 제안  
> **작성일:** 2026-04-11  
> **핵심:** 과거 프로젝트 자료(intranet_projects)와 제안서 완료 자료(archive) 통합 관리

---

## 🔄 프로젝트 생명주기 (상태 정의)

### 독립적 상태 변수 (3개)

```
┌─────────────────────────────────────────────────────────────┐
│               제안 프로젝트 생명주기 (상태 분리)               │
└─────────────────────────────────────────────────────────────┘

◆ proposal_status (제안 상태 - 모든 프로젝트)
  DRAFT → SUBMITTED → RESULT_ANNOUNCED

◆ result_status (수주 결과 - active_proposal만)
  PENDING (대기) → WON (성공) or LOST (실패)

◆ execution_status (수행 상태 - result_status=WON인 경우만)
  NULL → IN_PROGRESS → COMPLETED

예시:
  active_proposal: proposal_status=SUBMITTED, result_status=PENDING, execution_status=NULL
  completed_proposal (수주성공): proposal_status=RESULT_ANNOUNCED, result_status=WON, execution_status=IN_PROGRESS
  completed_proposal (수주실패): proposal_status=RESULT_ANNOUNCED, result_status=LOST, execution_status=NULL
```

### 상태 값 정의

| 변수 | 가능한 값 | 설명 |
|------|---------|------|
| **proposal_status** | DRAFT | 제안서 작업 중 |
| | SUBMITTED | 제안서 제출 완료 |
| | RESULT_ANNOUNCED | 결과 발표됨 |
| **result_status** | PENDING | 수주 결과 대기 중 |
| | WON | 수주 성공 |
| | LOST | 수주 실패 |
| **execution_status** | IN_PROGRESS | 수행 중 (result_status=WON인 경우만) |
| | COMPLETED | 수행 종료 (result_status=WON인 경우만) |
| | NULL | 해당 없음 (result_status≠WON인 경우) |

---

## 🎯 핵심 고민

### 현재 상황
```
intranet_projects (과거 실제 수행 프로젝트)
  ├── 프로젝트명, 발주처, 예산, 팀명
  ├── **실제 참여 연구원** ← 프로젝트 수행에 실제 참여한 사람들
  └── 문서 자료 (제안서 등)

proposals (현재/진행 중인 제안서)
  ├── RFP 내용, 제안 전략
  ├── **제안 작성 참여자** ← 제안서를 작성한 사람들 (다를 수 있음!)
  └── project_archive (산출물)
      ├── 완성된 제안서
      ├── 분석 자료
      └── 발표 자료
```

### 문제점
1. **참여자 구분 필요**
   - 실제 프로젝트 참여연구원 vs 제안 작성 참여자
   - DB 필드가 달라야 함

2. **두 시스템의 통합 여부**
   - 분리: 독립적이지만 연계 복잡
   - 통합: 구조 복잡하지만 강력함

3. **Storage 경로 일관성**
   - intranet_projects의 문서
   - proposals의 archive 산출물
   - 같은 계층 구조?

---

## ✅ 통합 설계안

### 옵션 A: 완전 통합 (권장)

단일 `master_projects` 테이블로 모든 프로젝트 관리:

```sql
CREATE TABLE master_projects (
    id                      UUID PRIMARY KEY,
    org_id                  UUID NOT NULL,
    
    -- 기본 정보
    project_name            TEXT NOT NULL,
    project_year            INTEGER,
    client_name             TEXT,
    
    -- 요약/내용
    summary                 TEXT,              -- 주요 내용 요약
    description             TEXT,
    
    -- 기간
    start_date              DATE,
    end_date                DATE,
    
    -- 재정 정보
    budget_krw              BIGINT,
    
    -- 프로젝트 유형
    project_type            TEXT NOT NULL,    -- 'historical' | 'active_proposal' | 'completed_proposal'
        CHECK (project_type IN ('historical', 'active_proposal', 'completed_proposal')),
    
    -- 상태 (독립적 3개 변수)
    proposal_status         TEXT,              -- DRAFT | SUBMITTED | RESULT_ANNOUNCED (제안 상태)
        CHECK (proposal_status IN ('DRAFT', 'SUBMITTED', 'RESULT_ANNOUNCED')),
    result_status           TEXT,              -- PENDING | WON | LOST (수주 결과, active_proposal만)
        CHECK (result_status IN ('PENDING', 'WON', 'LOST')),
    execution_status        TEXT,              -- IN_PROGRESS | COMPLETED (수행 상태, result_status=WON인 경우만)
        CHECK (execution_status IN ('IN_PROGRESS', 'COMPLETED'))
    
    -- === historical 프로젝트 전용 필드 ===
    legacy_idx              INTEGER,           -- MSSQL idx_no
    legacy_code             TEXT,              -- MSSQL pr_code
    
    -- === proposal 연동 필드 ===
    proposal_id             UUID REFERENCES proposals(id),  -- active/completed만 존재
    
    -- === 참여자 정보 (두 그룹 분리!) ===
    -- 그룹 1: 용역수행팀 + 팀원 (intranet_projects)
    actual_teams            JSONB,             -- 수행팀들 [{team_id, team_name}] (1개 이상)
    actual_participants     JSONB,             -- 팀원들 [{name, role, team_id, years_involved}] (여러명)
    
    -- 그룹 2: 제안팀 + 제안작업참여자 (proposals)
    proposal_teams          JSONB,             -- 제안팀들 [{team_id, team_name}] (1개 이상)
    proposal_participants   JSONB,             -- 제안작업참여자 [{user_id, name, role, team_id}] (여러명)
    
    -- 문서 & 자료
    document_count          INTEGER DEFAULT 0,
    archive_count           INTEGER DEFAULT 0,  -- proposals의 산출물 수
    
    -- 검색 필드
    keywords                TEXT[],
    embedding               vector(1536),
    
    -- 감사
    created_at              TIMESTAMPTZ,
    updated_at              TIMESTAMPTZ,
    
    -- 제약
    UNIQUE(org_id, legacy_idx) WHERE project_type = 'historical',
    UNIQUE(proposal_id) WHERE proposal_id IS NOT NULL
);

-- 인덱스
CREATE INDEX idx_master_projects_org ON master_projects(org_id);
CREATE INDEX idx_master_projects_type ON master_projects(project_type);
CREATE INDEX idx_master_projects_proposal ON master_projects(proposal_id) WHERE proposal_id IS NOT NULL;
CREATE INDEX idx_master_projects_year ON master_projects(project_year);
```

### Storage 경로 통합

```
projects/
  └── {master_project_id}/                    # 불변 ID
      ├── metadata/
      │   ├── project-info.json               # 프로젝트 기본 정보
      │   ├── actual-team.json                # 실제 참여 팀/인원
      │   └── proposal-team.json              # 제안 작성 팀/인원 (있으면)
      │
      ├── intranet-documents/                 # 과거 자료 (historical)
      │   ├── proposal.pdf
      │   ├── report.pdf
      │   └── extracted-text.txt
      │
      ├── proposal-archive/                   # 제안서 산출물 (proposal)
      │   ├── rfp/
      │   │   └── rfp.pdf
      │   ├── analysis/
      │   │   ├── compliance-matrix.xlsx
      │   │   └── analysis.md
      │   ├── strategy/
      │   │   └── strategy.md
      │   ├── proposal/
      │   │   ├── proposal.docx
      │   │   └── proposal.hwpx
      │   └── presentation/
      │       └── presentation.pptx
      │
      └── extracted-text/
          ├── intranet-docs.txt
          └── proposal.txt
```

---

## 📊 DB 테이블 구조 (통합 설계)

### 1. master_projects (신규)
모든 프로젝트의 단일 진실 공급원 (SSOT)

```sql
id                      -- master_project_id (불변)
org_id
project_name
project_year
start_date              -- 프로젝트 시작일
end_date                -- 프로젝트 종료일
client_name
summary                 -- 주요 내용 요약
budget_krw
project_type           -- historical | active_proposal | completed_proposal
proposal_status        -- DRAFT | SUBMITTED | RESULT_ANNOUNCED
result_status          -- PENDING | WON | LOST (active_proposal만)
execution_status       -- IN_PROGRESS | COMPLETED (result_status=WON인 경우만)
legacy_idx             -- ← intranet_projects 출처
legacy_code
proposal_id            -- ← proposals 연동
actual_teams           -- ← 수행팀들 [{team_id, team_name}] (1개 이상)
actual_participants    -- ← 팀원들 [{name, role, team_id, years_involved}] (여러명)
proposal_teams         -- ← 제안팀들 [{team_id, team_name}] (1개 이상)
proposal_participants  -- ← 제안작업참여자 [{user_id, name, role, team_id}] (여러명, 내부 직원 ID)
document_count
archive_count
keywords
embedding
created_at
updated_at
```

### 2. intranet_documents (수정)
master_projects와 연결

```sql
id
master_project_id       -- ← 변경: org_id/document_id 대신
project_id             -- ← 폐기 (NULL 가능하지만 master_project_id 사용)
org_id
doc_type              -- proposal, report, reference, etc.
filename
storage_path          -- projects/{master_project_id}/intranet-documents/{filename}
extracted_text
processing_status
...
```

### 3. project_archive (유지 - 링크 추가)
proposals와 master_projects 모두 참조

```sql
id
proposal_id           -- ← 기존 (proposals와의 관계)
master_project_id     -- ← 신규 추가 (master_projects와의 관계)
org_id
category
doc_type
title
storage_path          -- projects/{master_project_id}/proposal-archive/{category}/{filename}
...
```

### 4. proposals (유지 - 링크 추가)
master_projects과 양방향 연결

```sql
id
master_project_id     -- ← 신규: master_projects와의 1:1 연결
org_id
title
status
...
```

---

## 🔄 데이터 흐름

### 흐름 1: Historical 프로젝트 + 자료
```
MSSQL Project_List
  ↓
intranet_projects 마이그레이션
  ↓
master_projects (project_type='historical')
  ├── actual_teams (1개 이상), actual_participants 저장
  └── intranet_documents 연결
```

### 흐름 2: 새 제안서 작성 (RFP → 완료)
```
proposal 생성 (제안서 시작)
  ↓
master_projects (project_type='active_proposal')
  ├── proposal_id 연결
  ├── proposal_teams (1개 이상), proposal_participants 저장
  └── intranet_documents (선택적: 참고 자료)

proposal 완료
  ↓
project_archive 저장
  ├── master_project_id 저장
  └── status 변경: project_type='completed_proposal'
```

### 흐름 3: 과거 자료 재활용
```
검색: keyword='AI'
  ↓
master_projects 검색
  ├── historical 유형 (과거 수행 프로젝트)
  │   ├── intranet_documents 조회
  │   ├── actual_teams 표시 (1개 이상)
  │   └── actual_participants 표시
  │
  └── completed_proposal 유형 (완료된 제안서)
      ├── project_archive 조회
      ├── proposal_teams 표시 (1개 이상)
      └── proposal_participants 표시
```

---

## 📋 메타데이터 필드 정의

### master_projects.metadata (JSON)
```json
{
  "project_id": "2c59535a-1a27-47e3-8ff8-550f76a819af",
  "project_name": "AI 기반 제안서 자동 작성 플랫폼",
  "project_year": 2025,
  "start_date": "2025-01-15",
  "end_date": "2025-12-31",
  "summary": "국방부 요구에 따른 AI 기반 자동화 솔루션...",
  "client_name": "국방부",
  "budget_krw": 500000000,
  "keywords": ["AI", "NLP", "자동화", "문서생성"],
  
  "actual_teams": [
    {"team_id": "team-ai", "team_name": "AI팀"},
    {"team_id": "team-infra", "team_name": "인프라팀"}
  ],
  
  "actual_participants": [
    {"name": "김철수", "role": "PM", "team_id": "team-ai", "years_involved": 2},
    {"name": "이영희", "role": "Developer", "team_id": "team-ai", "years_involved": 2},
    {"name": "박준호", "role": "Researcher", "team_id": "team-ai", "years_involved": 1},
    {"name": "정수영", "role": "Infrastructure", "team_id": "team-infra", "years_involved": 1}
  ],
  
  "proposal_teams": [
    {"team_id": "team-ai", "team_name": "AI팀"},
    {"team_id": "team-sales", "team_name": "기술영업팀"}
  ],
  
  "proposal_participants": [
    {"user_id": "EMP001", "name": "김철수", "role": "Lead Writer", "team_id": "team-ai"},
    {"user_id": "EMP002", "name": "이영희", "role": "Reviewer", "team_id": "team-ai"},
    {"user_id": "EMP045", "name": "최민수", "role": "Sales Lead", "team_id": "team-sales"}
  ],
  
  "project_type": "historical",
  "proposal_status": "RESULT_ANNOUNCED",
  "result_status": null,
  "execution_status": null
}
```

---

## API 엔드포인트

### 프로젝트 검색 (통합)
```typescript
GET /api/master-projects?keyword=AI&year=2025&type=historical,completed_proposal

Response:
[
  {
    id: "2c59535a-1a27-47e3-8ff8-550f76a819af",
    project_name: "AI 기반 제안서 자동 작성 플랫폼",
    summary: "...",
    client_name: "국방부",
    budget_krw: 500000000,
    project_type: "historical",
    proposal_status: "RESULT_ANNOUNCED",
    result_status: null,
    execution_status: null,
    
    // 참여자 정보 (타입에 따라 다름)
    actual_teams: [
      { team_id: "team-ai", team_name: "AI팀" }
    ],
    actual_participants: [...]  // historical이므로 있음
    
    proposal_teams: null,        // historical이므로 없음
    proposal_participants: null  // historical이므로 없음
    
    // 자료
    documents: [
      {
        type: "intranet",
        filename: "proposal.pdf",
        extracted_text: "...",
        storage_path: "projects/2c59535a-1a27.../intranet-documents/proposal.pdf"
      }
    ],
    archive: null  // historical이므로 없음
  }
]
```

### 프로젝트 상세 조회
```typescript
GET /api/master-projects/{projectId}

Response:
{
  ...
  proposal_status: "SUBMITTED",      // DRAFT | SUBMITTED | RESULT_ANNOUNCED
  result_status: "PENDING",          // PENDING | WON | LOST (active_proposal만)
  execution_status: null,            // IN_PROGRESS | COMPLETED (result_status=WON인 경우만)
  
  documents: [
    {id, filename, doc_type, extracted_text, storage_path}
  ],
  archive: [                         // project_type='completed_proposal'일 때만
    {id, category, title, storage_path, file_format}
  ],
  actual_teams: [                    // 용역수행팀들 (1개 이상)
    {team_id, team_name}
  ],
  actual_participants: [             // 팀원들 (여러명)
    {name, role, team_id, years_involved}
  ],
  proposal_teams: [                  // 제안팀들 (1개 이상)
    {team_id, team_name}
  ],
  proposal_participants: [           // 제안작업참여자 (여러명)
    {user_id, name, role, team_id}
  ]
}
```

---

## 💾 마이그레이션 전략

### Phase 1: master_projects 테이블 생성 (즉시)
```sql
CREATE TABLE master_projects (...)
```

### Phase 2: 기존 데이터 이관
```sql
-- intranet_projects → master_projects (historical만)
INSERT INTO master_projects (...)
SELECT 
  id,
  org_id,
  project_name,
  client_name,
  budget_krw,
  'historical' as project_type,
  'RESULT_ANNOUNCED' as proposal_status,  -- 과거 완료 프로젝트
  null as result_status,
  null as execution_status,
  actual_teams,           -- 복수 팀 배열
  actual_participants,    -- 복수 인원 배열
  ...
FROM intranet_projects;

-- proposals → master_projects (필요시)
-- ※ 선택적: proposal만 진행 중인 경우
```

### Phase 3: 외래키 업데이트
```sql
-- intranet_documents → master_project_id
ALTER TABLE intranet_documents ADD COLUMN master_project_id UUID;
UPDATE intranet_documents SET master_project_id = ... FROM intranet_projects;

-- project_archive → master_project_id
ALTER TABLE project_archive ADD COLUMN master_project_id UUID;
UPDATE project_archive SET master_project_id = ... FROM proposals JOIN master_projects;
```

### Phase 4: API 업데이트
- 검색 API → master_projects 기반
- 다운로드 API → 통합 경로 사용
- 프로젝트 상세 → 두 참여자 그룹 모두 표시

---

## 🔍 구현 체크리스트

- [ ] **DB 설계**
  - [ ] master_projects 테이블 생성
  - [ ] 상태 필드 3개 분리: proposal_status, result_status, execution_status
  - [ ] actual_teams, actual_participants 필드 정의 (복수 팀/인원)
  - [ ] proposal_teams, proposal_participants 필드 정의 (복수 팀/인원)
  - [ ] storage_path 통일

- [ ] **데이터 마이그레이션**
  - [ ] intranet_projects → master_projects (historical)
  - [ ] intranet_documents → master_project_id 업데이트
  - [ ] project_archive → master_project_id 추가

- [ ] **파일 마이그레이션**
  - [ ] org_id 기반 경로 → projects/{id}/ 로 변경
  - [ ] intranet-documents/ vs proposal-archive/ 폴더 분리

- [ ] **API 개발**
  - [ ] GET /api/master-projects (검색)
  - [ ] GET /api/master-projects/{id} (상세)
  - [ ] GET /api/master-projects/{id}/documents (문서)
  - [ ] GET /api/master-projects/{id}/download (다운로드)

- [ ] **프론트엔드**
  - [ ] 통합 검색 UI
  - [ ] 프로젝트 상세 페이지 (두 참여자 그룹 표시)
  - [ ] 문서/아카이브 탭 표시

---

## ✨ 장점

| 항목 | 효과 |
|------|------|
| **통합 검색** | 과거 프로젝트 + 제안서 자료 한 곳에서 검색 🔍 |
| **참여자 구분** | 실제 수행인원 vs 제안 작성인원 명확 👥 |
| **확장성** | 향후 다른 자료 유형 추가 용이 🚀 |
| **데이터 무결성** | 단일 테이블로 관리하면서도 구조 명확 🔒 |
| **조직 변경 무영향** | master_project_id는 불변 🛡️ |

---

## 예시: 완전한 사용 시나리오

### 검색
```
사용자: "AI 관련 과제 찾아줘"
  ↓
master_projects 검색 (keyword contains 'AI')
  ↓
결과:
  1. historical: AI 기반 제안서 자동 작성 (2025, 국방부)
     - 수행팀: AI팀, 인프라팀
     - 팀원: 김철수(AI팀 PM), 이영희(AI팀 Developer), 박준호(AI팀 Researcher), 정수영(인프라팀 Engineer)
     - 예산: 5억
     - 문서: proposal.pdf, report.pdf
  
  2. completed_proposal: AI 마이크로칩 설계 (2025, 방위사업청)
     - 제안팀: AI팀, 기술영업팀
     - 제안참여자: 김철수(AI팀 Lead Writer), 이영희(AI팀 Reviewer), 최민수(기술영업팀 Sales Lead)
     - 아카이브: 제안서.docx, 발표자료.pptx
```

### 다운로드
```
사용자: "첫번째 프로젝트의 제안서 다운로드"
  ↓
GET /api/master-projects/{id}/documents/{docId}/download
  ↓
Signed URL 반환:
  projects/2c59535a-1a27-47e3-8ff8-550f76a819af/
    intranet-documents/proposal.pdf
```

---

## 다음 단계

1. **설계 검토** → 조직 변경 영향도 재검토
2. **prototype** → 소수 프로젝트로 DB 설계 테스트
3. **마이그레이션** → 전체 데이터 이관
4. **API 구현** → 통합 검색/다운로드 엔드포인트
5. **운영** → 신규 제안서부터 master_projects 직접 생성

