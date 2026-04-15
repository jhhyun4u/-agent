# 4. 제안 프로젝트 (`/proposals`) & 4-A. 목록 (`/proposals`)
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **4. 제안 프로젝트 (`/proposals`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 5 connections
  - -> contains -> [[4-a-proposals]]
  - -> contains -> [[4-b-proposalsnew]]
  - -> contains -> [[4-c-proposalsid]]
  - -> contains -> [[4-d-proposalsidedit]]
  - -> contains -> [[4-e-proposalsidevaluation]]
- **4-A. 목록 (`/proposals`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-B. 신규 생성 (`/proposals/new`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-C. 상세 (`/proposals/[id]`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-D. 편집 (`/proposals/[id]/edit`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[4-proposals]]
- **4-E. 모의평가 (`/proposals/[id]/evaluation`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[4-proposals]]

## Internal Relationships
- 4. 제안 프로젝트 (`/proposals`) -> contains -> 4-A. 목록 (`/proposals`) [EXTRACTED]
- 4. 제안 프로젝트 (`/proposals`) -> contains -> 4-B. 신규 생성 (`/proposals/new`) [EXTRACTED]
- 4. 제안 프로젝트 (`/proposals`) -> contains -> 4-C. 상세 (`/proposals/[id]`) [EXTRACTED]
- 4. 제안 프로젝트 (`/proposals`) -> contains -> 4-D. 편집 (`/proposals/[id]/edit`) [EXTRACTED]
- 4. 제안 프로젝트 (`/proposals`) -> contains -> 4-E. 모의평가 (`/proposals/[id]/evaluation`) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 4. 제안 프로젝트 (`/proposals`), 4-A. 목록 (`/proposals`), 4-B. 신규 생성 (`/proposals/new`)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test-checklist-frontend.md이다.

### Key Facts
- 4-A. 목록 (`/proposals`)
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 4A-1 | 프로젝트 목록 테이블: 5개 컬럼 (제목, 상태, 마감, 단계, 수정일) | ☐ | | 4A-2 | 상태 필터 (전체/진행/완료/보관) | ☐ | | 4A-3 | 검색: 제목 키워드 검색 | ☐ | | 4A-4 | "새 프로젝트" 버튼 → `/proposals/new` | ☐ | | 4A-5 | 행 클릭 → `/proposals/[id]` 상세 | ☐ | | 4A-6 | 빈 상태: 프로젝트 없을 때 안내 | ☐ |
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 4B-1 | 3가지 진입 경로 선택 UI | ☐ | | 4B-2 | 공고 번호로 생성 → G2B 연동 | ☐ | | 4B-3 | 수동 입력으로 생성 | ☐ | | 4B-4 | RFP 파일 업로드로 생성 | ☐ | | 4B-5 | 생성 성공 → 프로젝트 상세 이동 | ☐ |
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 4C-1 | ProjectContextHeader: 제목, 상태, 마감일 표시 | ☐ | | 4C-2 | StreamProgressHeader: 3-Stream 진행률 | ☐ | | 4C-3 | StreamTabBar: 탭 전환 (제안서/제출서류/투찰) | ☐ | | 4C-4 | PhaseGraph: 워크플로 단계 시각화 | ☐ | | 4C-5 | WorkflowPanel: 현재 단계 + 시작/재개 버튼 | ☐ | | 4C-6 |…
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 4D-1 | ProposalEditor: 3-column 레이아웃 (TOC/에디터/AI) | ☐ | | 4D-2 | EditorTocPanel: 목차 + Compliance 요약 | ☐ | | 4D-3 | 목차 항목 클릭 → 해당 섹션 스크롤 | ☐ | | 4D-4 | Tiptap 에디터: 텍스트 편집 (볼드/이탤릭/헤딩 등) | ☐ | | 4D-5 | EditorAiPanel: AI 질문 입력 → 응답 표시 | ☐ | | 4D-6 |…
