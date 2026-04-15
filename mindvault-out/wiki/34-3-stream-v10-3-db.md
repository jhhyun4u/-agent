# §34. 3-Stream 병행 업무 설계 (v1.0) & 3. DB 스키마
Cohesion: 0.10 | Nodes: 21

## Key Nodes
- **§34. 3-Stream 병행 업무 설계 (v1.0)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-option-c-hybrid]]
  - -> contains -> [[3-db]]
  - -> contains -> [[4]]
  - -> contains -> [[5-api-16]]
  - -> contains -> [[6]]
  - -> contains -> [[7-ui]]
  - -> contains -> [[8]]
- **3. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 5 connections
  - -> contains -> [[3-1-submissiondocuments-stream-3]]
  - -> contains -> [[3-2-streamprogress]]
  - -> contains -> [[3-3-orgdocumenttemplates]]
  - -> contains -> [[3-4-proposals]]
  - <- contains <- [[34-3-stream-v10]]
- **4. 백엔드 서비스** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 4 connections
  - -> contains -> [[4-1-streamorchestratorpy]]
  - -> contains -> [[4-2-submissiondocsservicepy]]
  - -> contains -> [[4-3-biddingstreampy]]
  - <- contains <- [[34-3-stream-v10]]
- **5. API 엔드포인트 (16개)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 4 connections
  - -> contains -> [[5-1-3]]
  - -> contains -> [[5-2-8-3]]
  - -> contains -> [[5-3-2]]
  - <- contains <- [[34-3-stream-v10]]
- **7. 프론트엔드 UI** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 3 connections
  - -> contains -> [[7-1]]
  - -> contains -> [[7-2]]
  - <- contains <- [[34-3-stream-v10]]
- **1. 개요** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[34-3-stream-v10]]
- **2. 아키텍처 결정: Option C Hybrid** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[34-3-stream-v10]]
- **3-1. `submission_documents` (Stream 3)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[3-db]]
- **3-2. `stream_progress` (오케스트레이션)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[3-db]]
- **3-3. `org_document_templates` (조직 공통 서류)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[3-db]]
- **3-4. `proposals` 확장** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[3-db]]
- **4-1. `stream_orchestrator.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[4]]
- **4-2. `submission_docs_service.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[4]]
- **4-3. `bidding_stream.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[4]]
- **5-1. 스트림 오케스트레이션 (3개)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[5-api-16]]
- **5-2. 제출서류 (8개) + 조직 공통 서류 (3개)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[5-api-16]]
- **5-3. 비딩 확장 (2개)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[5-api-16]]
- **6. 그래프 통합 (최소 변경)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[34-3-stream-v10]]
- **7-1. 인프라 컴포넌트** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[7-ui]]
- **7-2. 탭별 컨텐츠** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[7-ui]]
- **8. 합류 규칙** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\three-streams.design.md) -- 1 connections
  - <- contains <- [[34-3-stream-v10]]

## Internal Relationships
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 1. 개요 [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 2. 아키텍처 결정: Option C Hybrid [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 3. DB 스키마 [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 4. 백엔드 서비스 [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 5. API 엔드포인트 (16개) [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 6. 그래프 통합 (최소 변경) [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 7. 프론트엔드 UI [EXTRACTED]
- §34. 3-Stream 병행 업무 설계 (v1.0) -> contains -> 8. 합류 규칙 [EXTRACTED]
- 3. DB 스키마 -> contains -> 3-1. `submission_documents` (Stream 3) [EXTRACTED]
- 3. DB 스키마 -> contains -> 3-2. `stream_progress` (오케스트레이션) [EXTRACTED]
- 3. DB 스키마 -> contains -> 3-3. `org_document_templates` (조직 공통 서류) [EXTRACTED]
- 3. DB 스키마 -> contains -> 3-4. `proposals` 확장 [EXTRACTED]
- 4. 백엔드 서비스 -> contains -> 4-1. `stream_orchestrator.py` [EXTRACTED]
- 4. 백엔드 서비스 -> contains -> 4-2. `submission_docs_service.py` [EXTRACTED]
- 4. 백엔드 서비스 -> contains -> 4-3. `bidding_stream.py` [EXTRACTED]
- 5. API 엔드포인트 (16개) -> contains -> 5-1. 스트림 오케스트레이션 (3개) [EXTRACTED]
- 5. API 엔드포인트 (16개) -> contains -> 5-2. 제출서류 (8개) + 조직 공통 서류 (3개) [EXTRACTED]
- 5. API 엔드포인트 (16개) -> contains -> 5-3. 비딩 확장 (2개) [EXTRACTED]
- 7. 프론트엔드 UI -> contains -> 7-1. 인프라 컴포넌트 [EXTRACTED]
- 7. 프론트엔드 UI -> contains -> 7-2. 탭별 컨텐츠 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 §34. 3-Stream 병행 업무 설계 (v1.0), 3. DB 스키마, 4. 백엔드 서비스를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 three-streams.design.md이다.

### Key Facts
- **작성일**: 2026-03-21 **상태**: 구현 완료 (Match Rate 98%)
- 3-1. `submission_documents` (Stream 3)
- 4-1. `stream_orchestrator.py`
- 5-1. 스트림 오케스트레이션 (3개)
- Go/No-Go 결정 이후 3가지 업무가 병행 진행되는 구조:
