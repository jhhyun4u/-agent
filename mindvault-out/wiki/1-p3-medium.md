# 🟡 주의 항목 (1개) & 🟢 P3 (Medium) — 운영 기능, 여유 시간에
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **🟡 주의 항목 (1개)** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 4 connections
  - -> contains -> [[testworkflowaistatus]]
  - -> contains -> [[p1-critical]]
  - -> contains -> [[p2-high]]
  - -> contains -> [[p3-medium]]
- **🟢 P3 (Medium) — 운영 기능, 여유 시간에** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[1]]
- **bash** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- has_code_example <- [[p3-medium]]
- **🔴 P1 (Critical) — 핵심 기능, 즉시 고정** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[1]]
- **🟡 P2 (High) — 중요 기능, 이번 주 내** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[1]]
- **test_workflow_ai_status** (C:\project\tenopa proposer\-agent-master\TEST_REPORT.md) -- 1 connections
  - <- contains <- [[1]]

## Internal Relationships
- 🟡 주의 항목 (1개) -> contains -> test_workflow_ai_status [EXTRACTED]
- 🟡 주의 항목 (1개) -> contains -> 🔴 P1 (Critical) — 핵심 기능, 즉시 고정 [EXTRACTED]
- 🟡 주의 항목 (1개) -> contains -> 🟡 P2 (High) — 중요 기능, 이번 주 내 [EXTRACTED]
- 🟡 주의 항목 (1개) -> contains -> 🟢 P3 (Medium) — 운영 기능, 여유 시간에 [EXTRACTED]
- 🟢 P3 (Medium) — 운영 기능, 여유 시간에 -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 🟡 주의 항목 (1개), 🟢 P3 (Medium) — 운영 기능, 여유 시간에, bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 TEST_REPORT.md이다.

### Key Facts
- test_workflow_ai_status ``` ⚠️  XFAIL (async generator issue) 원인: AI 상태 조회가 async generator 기반이어서 mock 어려움 현재 상태: 예상된 실패로 표시 (xfail) 영향: AI 작업 상태 실시간 추적 (운영 기능) ```
- **테스트 실행 명령어:** ```bash 전체 테스트 uv run pytest tests/test_phase*.py -v
- 🟡 P2 (High) — 중요 기능, 이번 주 내 - **test_list_project_files**: Phase 10 fixture 개선 - **test_save_artifact_increments_version**: artifact mock 추가 - **test_delete_proposal**: CASCADE mock behavior 정의 - **예상 시간**: 30분 - **영향**: 파일 관리, 버전 관리
- 🟢 P3 (Medium) — 운영 기능, 여유 시간에 - **test_delete_running_proposal_blocked**: 안전장치 검증 - **test_workflow_ai_status**: async generator 리팩토링 - **예상 시간**: 45분 - **영향**: 안전장치, 실시간 상태 추적
- **해결 시점**: Phase 7 workflow async 리팩토링 시
