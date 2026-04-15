# (기존 16개 + 신규 6개 → 10개 Business Status) & 3-레이어 아키텍처
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **(기존 16개 + 신규 6개 → 10개 Business Status)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 1 connections
  - -> contains -> [[3]]
- **3-레이어 아키텍처** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[16-6-10-business-status]]

## Internal Relationships
- (기존 16개 + 신규 6개 → 10개 Business Status) -> contains -> 3-레이어 아키텍처 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 (기존 16개 + 신규 6개 → 10개 Business Status), 3-레이어 아키텍처를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 unified-state-system.plan.md이다.

### Key Facts
- > **작성일**: 2026-03-29 > **마이그레이션 기간**: 3-4일 > **설계 문서**: `docs/02-design/proposal-integrated-workflow-v5.0.md` > **상태**: 계획 수립 완료
- 핵심 변화 | 영역 | 기존 | 신규 | |------|------|------| | Status 값 | 16개 (상태 산재) | **10개** (통합) + win_result (세부) | | DB 제약 | CHECK constraint에서 모순 | 전체 재정의 | | 타임스탐프 | 생성/수정만 | **8개** (단계별 이벤트) | | 추적 테이블 | 없음 | proposal_timelines (이벤트 로그) | | AI 상태 | status에 혼입 (running, failed) | **ai_task_status 분리** |
