# 10. Admin (`/admin/*`) — admin/manager 전용 & 10-A. 이용자 관리 (`/admin`)
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **10. Admin (`/admin/*`) — admin/manager 전용** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 3 connections
  - -> contains -> [[10-a-admin]]
  - -> contains -> [[10-b-adminprompts]]
  - -> contains -> [[10-c-ab-adminpromptsexperiments]]
- **10-A. 이용자 관리 (`/admin`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[10-admin-admin-adminmanager]]
- **10-B. 프롬프트 관리 (`/admin/prompts`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[10-admin-admin-adminmanager]]
- **10-C. A/B 실험 (`/admin/prompts/experiments`)** (C:\project\tenopa proposer\-agent-master\docs\test-checklist-frontend.md) -- 1 connections
  - <- contains <- [[10-admin-admin-adminmanager]]

## Internal Relationships
- 10. Admin (`/admin/*`) — admin/manager 전용 -> contains -> 10-A. 이용자 관리 (`/admin`) [EXTRACTED]
- 10. Admin (`/admin/*`) — admin/manager 전용 -> contains -> 10-B. 프롬프트 관리 (`/admin/prompts`) [EXTRACTED]
- 10. Admin (`/admin/*`) — admin/manager 전용 -> contains -> 10-C. A/B 실험 (`/admin/prompts/experiments`) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 10. Admin (`/admin/*`) — admin/manager 전용, 10-A. 이용자 관리 (`/admin`), 10-B. 프롬프트 관리 (`/admin/prompts`)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test-checklist-frontend.md이다.

### Key Facts
- 10-A. 이용자 관리 (`/admin`)
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 10A-1 | AdminOrgChart: 조직도 렌더링 (본부/팀/사용자) | ☐ | | 10A-2 | 사용자 목록 + 역할 표시 | ☐ | | 10A-3 | 사용자 추가 (이메일 초대) | ☐ | | 10A-4 | 사용자 역할 변경 | ☐ | | 10A-5 | 사용자 비활성화 | ☐ | | 10A-6 | 조직/본부/팀 CRUD | ☐ |
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 10B-1 | 프롬프트 목록 (CategoryTabs) | ☐ | | 10B-2 | 프롬프트 상세 (`/admin/prompts/[promptId]`) | ☐ | | 10B-3 | PromptEditor: 프롬프트 편집 + 저장 | ☐ | | 10B-4 | PreviewPanel: 프롬프트 미리보기 | ☐ | | 10B-5 | CompareView: 버전 비교 | ☐ | | 10B-6 | 프롬프트 카탈로그…
- | # | 테스트 항목 | 확인 | |---|-----------|------| | 10C-1 | 실험 목록 렌더링 | ☐ | | 10C-2 | 새 실험 생성 | ☐ | | 10C-3 | 실험 결과 차트 (TrendChart, WinLossComparison) | ☐ | | 10C-4 | WorkflowMap: 프롬프트 워크플로 시각화 | ☐ |
