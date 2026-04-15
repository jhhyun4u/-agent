# javascript & 1. 마감일 모니터링
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **javascript** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 3 connections
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2-archive]]
  - <- has_code_example <- [[3-ai]]
- **1. 마감일 모니터링** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - -> has_code_example -> [[javascript]]
- **2. 자동 Archive 처리** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - -> has_code_example -> [[javascript]]
- **3. AI 상태 추적** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - -> has_code_example -> [[javascript]]

## Internal Relationships
- 1. 마감일 모니터링 -> has_code_example -> javascript [EXTRACTED]
- 2. 자동 Archive 처리 -> has_code_example -> javascript [EXTRACTED]
- 3. AI 상태 추적 -> has_code_example -> javascript [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 javascript, 1. 마감일 모니터링, 2. 자동 Archive 처리를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 proposal-workflow-states.md이다.

### Key Facts
- 1. 마감일 모니터링 ```javascript - D-7: 경고 (주황색) - D-3: 중요 (빨강색) - D-0: 초긍박 (깜빡이는 빨강) - D+1: 마감 경과 (회색 취소선) ```
- 2. 자동 Archive 처리 ```javascript // 매일 자정에 실행 - 종료 상태 → 30일 이상 경과 - status = 'archived' - updated_at 기록 - 목록에서 제외 ```
- 3. AI 상태 추적 ```javascript - 각 상태별 AI 지원 활성화/비활성화 - 진행 상태: 모든 AI 기능 활성화 - 완료/제출/발표/종료: AI 기능 비활성화 ```
