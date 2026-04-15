# Gap Analysis: 3-Stream 병행 업무 (three-streams) & Phase C~F 상세
Cohesion: 0.12 | Nodes: 16

## Key Nodes
- **Gap Analysis: 3-Stream 병행 업무 (three-streams)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 8 connections
  - -> contains -> [[overall-scores]]
  - -> contains -> [[red-missingbug-o-x-or]]
  - -> contains -> [[yellow-x-o]]
  - -> contains -> [[blue]]
  - -> contains -> [[phase-a]]
  - -> contains -> [[phase-b]]
  - -> contains -> [[phase-cf]]
  - -> contains -> [[match-rate]]
- **Phase C~F 상세** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 5 connections
  - -> contains -> [[c-frontend-infra]]
  - -> contains -> [[d-submissiondocspanel]]
  - -> contains -> [[e-biddingworkspace]]
  - -> contains -> [[f-streamdashboard]]
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **Phase A 상세** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 4 connections
  - -> contains -> [[a-1-db-migration]]
  - -> contains -> [[a-2]]
  - -> contains -> [[a-4-api]]
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **A-1. DB Migration** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-a]]
- **A-2. 백엔드 서비스** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-a]]
- **A-4. API 라우트** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-a]]
- **BLUE — 변경 사항 (설계 ≠ 구현)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **C: Frontend Infra** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-cf]]
- **D: SubmissionDocsPanel** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-cf]]
- **E: BiddingWorkspace** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-cf]]
- **F: StreamDashboard** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[phase-cf]]
- **Match Rate 산출** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **Overall Scores** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **Phase B 상세** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **RED — Missing/Bug (설계 O, 구현 X or 버그)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-3-stream-three-streams]]
- **YELLOW — 추가 기능 (설계 X, 구현 O)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\three-streams.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-3-stream-three-streams]]

## Internal Relationships
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> Overall Scores [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> RED — Missing/Bug (설계 O, 구현 X or 버그) [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> YELLOW — 추가 기능 (설계 X, 구현 O) [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> BLUE — 변경 사항 (설계 ≠ 구현) [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> Phase A 상세 [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> Phase B 상세 [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> Phase C~F 상세 [EXTRACTED]
- Gap Analysis: 3-Stream 병행 업무 (three-streams) -> contains -> Match Rate 산출 [EXTRACTED]
- Phase A 상세 -> contains -> A-1. DB Migration [EXTRACTED]
- Phase A 상세 -> contains -> A-2. 백엔드 서비스 [EXTRACTED]
- Phase A 상세 -> contains -> A-4. API 라우트 [EXTRACTED]
- Phase C~F 상세 -> contains -> C: Frontend Infra [EXTRACTED]
- Phase C~F 상세 -> contains -> D: SubmissionDocsPanel [EXTRACTED]
- Phase C~F 상세 -> contains -> E: BiddingWorkspace [EXTRACTED]
- Phase C~F 상세 -> contains -> F: StreamDashboard [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap Analysis: 3-Stream 병행 업무 (three-streams), Phase C~F 상세, Phase A 상세를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 three-streams.analysis.md이다.

### Key Facts
- **분석일**: 2026-03-21 **설계 기준**: 인라인 구현 계획서 (Phase A~F) **Match Rate**: **97%** (GAP-1 수정 후 **98%**)
- | 항목 | 설계 | 구현 | 상태 | |------|------|------|:----:| | `submission_documents` 테이블 | 전체 컬럼 | 전체 일치 + expired/template_matched 추가 | ✅ | | `stream_progress` 테이블 | 전체 컬럼 + UNIQUE | 전체 일치 | ✅ | | `org_document_templates` 테이블 | 전체 컬럼 + UNIQUE | 전체 일치 | ✅ | | `proposals` 확장 | streams_ready +…
- | 서비스 | 함수 수(설계) | 구현 | 상태 | |--------|:------:|:----:|:----:| | `stream_orchestrator.py` | 5 | 5 + 헬퍼 2 | ✅ | | `submission_docs_service.py` | 9 | 12 (add_document, delete_document 등 추가) | ✅ | | `bidding_stream.py` | 3 | 3 + 헬퍼 1 | ✅ |
- | 파일 | 엔드포인트(설계) | 구현 | 상태 | |------|:------:|:----:|:----:| | `routes_streams.py` | 3 | 3 | ✅ | | `routes_submission_docs.py` | 11 | 11 | ✅ | | `routes_bid_submission.py` 확장 | 2 | 2 | ✅ |
- | # | 항목 | 설계 | 구현 | 영향 | |---|------|------|------|------| | CHG-1 | Stream 1 완료 | END 후처리 | 별도 `stream1_complete_hook` 노드 → END | LOW (더 나은 설계) | | CHG-2 | 담당자 배정 UI | 팀원 선택 드롭다운 | 상태 변경만 (사용자 선택 미구현) | LOW |
