# email-notification v2.0 — 갭 분석 & GAP 목록
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **email-notification v2.0 — 갭 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.analysis.md) -- 2 connections
  - -> contains -> [[match-rate]]
  - -> contains -> [[gap]]
- **GAP 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.analysis.md) -- 1 connections
  - <- contains <- [[email-notification-v20]]
- **Match Rate** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.analysis.md) -- 1 connections
  - <- contains <- [[email-notification-v20]]

## Internal Relationships
- email-notification v2.0 — 갭 분석 -> contains -> Match Rate [EXTRACTED]
- email-notification v2.0 — 갭 분석 -> contains -> GAP 목록 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 email-notification v2.0 — 갭 분석, GAP 목록, Match Rate를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 email-notification.analysis.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | 분석일 | 2026-03-26 | | Design 참조 | docs/02-design/features/email-notification.design.md (v2.0) | | Match Rate | **97%** (38/39) |
- | ID | Severity | 파일 | 설명 | |----|----------|------|------| | BUG-1 | **MEDIUM** | `feedback_loop.py` | `create_notification()` 호출 시 `notification_type=` (잘못된 키워드) 사용 + `proposal_id` 매개변수 누락. 런타임 TypeError 발생. `type=`으로 변경 + `proposal_id` 추가 필요. (기존 코드의 pre-existing bug, 이메일 연동 추가와 무관) |
- | 항목 | 내용 | |------|------| | 분석일 | 2026-03-26 | | Design 참조 | docs/02-design/features/email-notification.design.md (v2.0) | | Match Rate | **97%** (38/39) |
