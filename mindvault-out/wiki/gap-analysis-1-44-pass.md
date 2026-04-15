# Gap Analysis: 배포 전 점검 체크리스트 커버리지 & 1. 핵심 비즈니스 로직 — 4/4 PASS
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **Gap Analysis: 배포 전 점검 체크리스트 커버리지** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\checklist-coverage.analysis.md) -- 5 connections
  - -> contains -> [[1-44-pass]]
  - -> contains -> [[2-253]]
  - -> contains -> [[3-api-253]]
  - -> contains -> [[4-ui-153]]
  - -> contains -> [[5-01-2-na]]
- **1. 핵심 비즈니스 로직 — 4/4 PASS** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\checklist-coverage.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis]]
- **2. 알림/경보 — 2.5/3** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\checklist-coverage.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis]]
- **3. API/데이터 — 2.5/3** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\checklist-coverage.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis]]
- **4. UI 컴포넌트 — 1.5/3** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\checklist-coverage.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis]]
- **5. 엣지 케이스 — 0/1 + 2 N/A** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\checklist-coverage.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis]]

## Internal Relationships
- Gap Analysis: 배포 전 점검 체크리스트 커버리지 -> contains -> 1. 핵심 비즈니스 로직 — 4/4 PASS [EXTRACTED]
- Gap Analysis: 배포 전 점검 체크리스트 커버리지 -> contains -> 2. 알림/경보 — 2.5/3 [EXTRACTED]
- Gap Analysis: 배포 전 점검 체크리스트 커버리지 -> contains -> 3. API/데이터 — 2.5/3 [EXTRACTED]
- Gap Analysis: 배포 전 점검 체크리스트 커버리지 -> contains -> 4. UI 컴포넌트 — 1.5/3 [EXTRACTED]
- Gap Analysis: 배포 전 점검 체크리스트 커버리지 -> contains -> 5. 엣지 케이스 — 0/1 + 2 N/A [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap Analysis: 배포 전 점검 체크리스트 커버리지, 1. 핵심 비즈니스 로직 — 4/4 PASS, 2. 알림/경보 — 2.5/3를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 checklist-coverage.analysis.md이다.

### Key Facts
- > 분석일: 2026-03-22 | Match Rate: **78.1%**
- | # | 항목 | 상태 | 테스트 수 | 근거 | |---|------|:----:|:---------:|------| | 1-1 | 진도율 계산 | ✅ | 5 | `calc_progress()` + TestCalcProgress | | 1-2 | 예산 집행률 | ✅ | 4 | `calc_budget_rate()` + TestCalcBudgetRate | | 1-3 | D-day 잔여일 | ✅ | 16 | `calc_dday()` + `deadline_alert_level()` | | 1-4 | 상태 전환 | ✅ | 33 |…
- | # | 항목 | 상태 | 갭 | |---|------|:----:|-----| | 2-1 | 기한 초과 알림 | ✅ | — | | 2-2 | 예산 이상 감지 | ⚠️ | 계산만 가능, **알림 트리거 로직 미구현** | | 2-3 | 수신자 격리 | ✅ | — |
- | # | 항목 | 상태 | 갭 | |---|------|:----:|-----| | 3-1 | API 응답 구조 | ⚠️ | Pydantic 모델 검증 PASS, **HTTP 통합 xfail** (기존 인프라) | | 3-2 | 파일 업/다운 | ✅ | — | | 3-3 | 대시보드 집계 | ✅ | — |
- | # | 항목 | 상태 | 갭 | |---|------|:----:|-----| | 4-1 | 게이지 색상 | ⚠️ | 구현 O, **컴포넌트 테스트 미작성** | | 4-2 | 필터/정렬 | ⚠️ | 구현 O, **컴포넌트 테스트 미작성** | | 4-3 | 권한별 UI | ❌ | 백엔드 있으나 **프론트 테스트 없음** |
