# 관리자 가이드 (Admin Guide) & bash
Cohesion: 0.28 | Nodes: 9

## Key Nodes
- **관리자 가이드 (Admin Guide)** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 7 connections
  - -> has_code_example -> [[bash]]
  - -> has_code_example -> [[env]]
  - -> contains -> [[rbac]]
  - -> contains -> [[audit-log]]
  - -> contains -> [[grafana]]
  - -> contains -> [[sla]]
  - <- contains <- [[admin-guide]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 3 connections
  - <- has_code_example <- [[admin-guide]]
  - <- has_code_example <- [[audit-log]]
  - <- has_code_example <- [[sla]]
- **성능 기준 (SLA)** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 3 connections
  - -> has_code_example -> [[bash]]
  - -> has_code_example -> [[javascript]]
  - <- contains <- [[admin-guide]]
- **감사 로그 (Audit Log)** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[admin-guide]]
- **env** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 1 connections
  - <- has_code_example <- [[admin-guide]]
- **javascript** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 1 connections
  - <- has_code_example <- [[sla]]
- **admin-guide** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 1 connections
  - -> contains -> [[admin-guide]]
- **Grafana 대시보드** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 1 connections
  - <- contains <- [[admin-guide]]
- **액세스 제어 (RBAC)** (C:\project\tenopa proposer\-agent-master\docs\operations\admin-guide.md) -- 1 connections
  - <- contains <- [[admin-guide]]

## Internal Relationships
- admin-guide -> contains -> 관리자 가이드 (Admin Guide) [EXTRACTED]
- 관리자 가이드 (Admin Guide) -> has_code_example -> bash [EXTRACTED]
- 관리자 가이드 (Admin Guide) -> has_code_example -> env [EXTRACTED]
- 관리자 가이드 (Admin Guide) -> contains -> 액세스 제어 (RBAC) [EXTRACTED]
- 관리자 가이드 (Admin Guide) -> contains -> 감사 로그 (Audit Log) [EXTRACTED]
- 관리자 가이드 (Admin Guide) -> contains -> Grafana 대시보드 [EXTRACTED]
- 관리자 가이드 (Admin Guide) -> contains -> 성능 기준 (SLA) [EXTRACTED]
- 감사 로그 (Audit Log) -> has_code_example -> bash [EXTRACTED]
- 성능 기준 (SLA) -> has_code_example -> bash [EXTRACTED]
- 성능 기준 (SLA) -> has_code_example -> javascript [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 관리자 가이드 (Admin Guide), bash, 성능 기준 (SLA)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 admin-guide.md이다.

### Key Facts
- **버전**: 1.0 **대상**: 시스템 관리자, DevOps **마지막 수정**: 2026-04-08
- **Uptime 확인**: ```bash 명령줄에서: curl https://api.tenopa.io/health
- | 메트릭 | 목표 | 경고 | 심각 | |--------|------|------|------| | API 응답시간 (P95) | < 200ms | > 500ms | > 1s | | 에러율 | < 0.1% | > 1% | > 5% | | 데이터베이스 응답시간 | < 50ms | > 100ms | > 500ms | | 캐시 히트율 | > 80% | < 70% | < 50% | | CPU 사용률 | < 60% | > 80% | > 95% | | 메모리 사용률 | < 70% | > 85% | > 95% |
- **접근**: `/admin/audit-logs`
- **주요 환경 변수**: ```env Supabase SUPABASE_URL=https://xxxxx.supabase.co SUPABASE_KEY=eyxxxxx SUPABASE_PASSWORD=xxxxxx
