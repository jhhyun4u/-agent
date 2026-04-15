# 4-4. 프로젝트 상세 `/proposals/[id]` & 4. 제안 프로젝트 `/proposals`
Cohesion: 0.17 | Nodes: 12

## Key Nodes
- **4-4. 프로젝트 상세 `/proposals/[id]`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 6 connections
  - -> contains -> [[4-4a]]
  - -> contains -> [[4-4b-gono-go]]
  - -> contains -> [[4-4c]]
  - -> contains -> [[4-4d]]
  - -> contains -> [[4-4e-qa]]
  - <- contains <- [[4-proposals]]
- **4. 제안 프로젝트 `/proposals`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 6 connections
  - -> contains -> [[4-1]]
  - -> contains -> [[4-2-3]]
  - -> contains -> [[4-3-proposalsnew]]
  - -> contains -> [[4-4-proposalsid]]
  - -> contains -> [[4-5-proposalsidedit]]
  - -> contains -> [[4-6-proposalsidevaluation]]
- **4-1. 프로젝트 목록** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-2. 3가지 진입 경로** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-3. 새 프로젝트 생성 `/proposals/new`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-4a. 워크플로 탭** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-4-proposalsid]]
- **4-4b. Go/No-Go 패널** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-4-proposalsid]]
- **4-4c. 제출서류 탭** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-4-proposalsid]]
- **4-4d. 입찰 탭** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-4-proposalsid]]
- **4-4e. Q&A 탭** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-4-proposalsid]]
- **4-5. 제안서 편집 `/proposals/[id]/edit`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-6. 모의평가 `/proposals/[id]/evaluation`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[4-proposals]]

## Internal Relationships
- 4-4. 프로젝트 상세 `/proposals/[id]` -> contains -> 4-4a. 워크플로 탭 [EXTRACTED]
- 4-4. 프로젝트 상세 `/proposals/[id]` -> contains -> 4-4b. Go/No-Go 패널 [EXTRACTED]
- 4-4. 프로젝트 상세 `/proposals/[id]` -> contains -> 4-4c. 제출서류 탭 [EXTRACTED]
- 4-4. 프로젝트 상세 `/proposals/[id]` -> contains -> 4-4d. 입찰 탭 [EXTRACTED]
- 4-4. 프로젝트 상세 `/proposals/[id]` -> contains -> 4-4e. Q&A 탭 [EXTRACTED]
- 4. 제안 프로젝트 `/proposals` -> contains -> 4-1. 프로젝트 목록 [EXTRACTED]
- 4. 제안 프로젝트 `/proposals` -> contains -> 4-2. 3가지 진입 경로 [EXTRACTED]
- 4. 제안 프로젝트 `/proposals` -> contains -> 4-3. 새 프로젝트 생성 `/proposals/new` [EXTRACTED]
- 4. 제안 프로젝트 `/proposals` -> contains -> 4-4. 프로젝트 상세 `/proposals/[id]` [EXTRACTED]
- 4. 제안 프로젝트 `/proposals` -> contains -> 4-5. 제안서 편집 `/proposals/[id]/edit` [EXTRACTED]
- 4. 제안 프로젝트 `/proposals` -> contains -> 4-6. 모의평가 `/proposals/[id]/evaluation` [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 4-4. 프로젝트 상세 `/proposals/[id]`, 4. 제안 프로젝트 `/proposals`, 4-1. 프로젝트 목록를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-manual-test-checklist.md이다.

### Key Facts
- 4-4a. 워크플로 탭 - [ ] PhaseGraph 단계 시각화 - [ ] WorkflowPanel (시작/일시정지/재개) - [ ] 워크플로 시작 → 단계별 진행 확인 - [ ] WorkflowResumeBanner (중단된 워크플로 복구) - [ ] StepArtifactViewer (단계별 산출물 조회) - [ ] ArtifactReviewPanel (AI 산출물 리뷰)
- 4-1. 프로젝트 목록 - [ ] 페이지 정상 렌더링 - [ ] 프로젝트 5컬럼 리스트 (제목, 상태, 단계, 마감일, 담당) - [ ] 상태별 컬러 뱃지 표시 - [ ] 검색/필터 동작 - [ ] 페이지네이션 동작
- 4-2. 3가지 진입 경로 - [ ] "새 프로젝트 생성" 버튼 → `/proposals/new` - [ ] "공고에서 생성" (from-rfp) 경로 동작 - [ ] "검색에서 생성" (from-search) 경로 동작
- 4-3. 새 프로젝트 생성 `/proposals/new` - [ ] 생성 폼 렌더링 - [ ] 필수 필드 유효성 검증 - [ ] 생성 완료 → 프로젝트 상세로 이동
- 4-4. 프로젝트 상세 `/proposals/[id]` - [ ] ProjectContextHeader 표시 (프로젝트명, 상태, 마감일) - [ ] StreamTabBar 탭 전환 동작 - [ ] StreamProgressHeader 진행률 표시
