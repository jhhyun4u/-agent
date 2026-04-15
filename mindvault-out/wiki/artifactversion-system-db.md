# ARTIFACT_VERSION System 기획서 & DB 테이블
Cohesion: 0.11 | Nodes: 19

## Key Nodes
- **ARTIFACT_VERSION System 기획서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 9 connections
  - -> contains -> [[functional-requirements-fr]]
  - -> contains -> [[non-functional-requirements-nfr]]
  - -> contains -> [[db]]
  - -> contains -> [[state]]
  - -> contains -> [[phase-1-2]]
  - -> contains -> [[phase-2-2]]
  - -> contains -> [[phase-3-2-3]]
  - -> contains -> [[step-8a]]
  - -> contains -> [[uiux]]
- **DB 테이블** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 6 connections
  - -> has_code_example -> [[sql]]
  - -> contains -> [[migration]]
  - -> contains -> [[phase-1]]
  - -> contains -> [[phase-2]]
  - -> contains -> [[phase-3]]
  - <- contains <- [[artifactversion-system]]
- **Phase 3 검증** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 3 connections
  - -> references -> [[unresolvedrefcomprehensiveimplementationreview]]
  - -> references -> [[unresolvedrefmockevaluationhumanreviewfeedback]]
  - <- contains <- [[db]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 2 connections
  - <- has_code_example <- [[db]]
  - <- has_code_example <- [[migration]]
- **Migration 파일** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **State 모델** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[artifactversion-system]]
- **🎨 UI/UX 설계** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 2 connections
  - -> contains -> [[versionselectionmodal]]
  - <- contains <- [[artifactversion-system]]
- **__unresolved__::ref::comprehensive_implementation_review** () -- 1 connections
  - <- references <- [[phase-3]]
- **__unresolved__::ref::mock_evaluation_human_review_feedback** () -- 1 connections
  - <- references <- [[phase-3]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- has_code_example <- [[state]]
- **Functional Requirements (FR)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **Non-Functional Requirements (NFR)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **Phase 1 검증** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[db]]
- **Phase 1: 기본 버전 관리 (필수, 2일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **Phase 2 검증** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[db]]
- **Phase 2: 버전 선택 메커니즘 (권장, 2일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **Phase 3: 고급 기능 (선택, 2-3일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **🔗 STEP 8A와의 통합** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **VersionSelectionModal** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\artifact-version-system.plan.md) -- 1 connections
  - <- contains <- [[uiux]]

## Internal Relationships
- ARTIFACT_VERSION System 기획서 -> contains -> Functional Requirements (FR) [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> Non-Functional Requirements (NFR) [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> DB 테이블 [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> State 모델 [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> Phase 1: 기본 버전 관리 (필수, 2일) [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> Phase 2: 버전 선택 메커니즘 (권장, 2일) [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> Phase 3: 고급 기능 (선택, 2-3일) [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> 🔗 STEP 8A와의 통합 [EXTRACTED]
- ARTIFACT_VERSION System 기획서 -> contains -> 🎨 UI/UX 설계 [EXTRACTED]
- DB 테이블 -> has_code_example -> sql [EXTRACTED]
- DB 테이블 -> contains -> Migration 파일 [EXTRACTED]
- DB 테이블 -> contains -> Phase 1 검증 [EXTRACTED]
- DB 테이블 -> contains -> Phase 2 검증 [EXTRACTED]
- DB 테이블 -> contains -> Phase 3 검증 [EXTRACTED]
- Migration 파일 -> has_code_example -> sql [EXTRACTED]
- Phase 3 검증 -> references -> __unresolved__::ref::comprehensive_implementation_review [EXTRACTED]
- Phase 3 검증 -> references -> __unresolved__::ref::mock_evaluation_human_review_feedback [EXTRACTED]
- State 모델 -> has_code_example -> python [EXTRACTED]
- 🎨 UI/UX 설계 -> contains -> VersionSelectionModal [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 ARTIFACT_VERSION System 기획서, DB 테이블, Phase 3 검증를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 artifact-version-system.plan.md이다.

### Key Facts
- > **작성일**: 2026-03-30 > **목표**: 노드 간 자유 이동 시 산출물 버전 관리 및 의존성 해결 시스템 구현 > **선행 요구사항**: COMPREHENSIVE-IMPLEMENTATION-REVIEW.md (노드 의존성 맵 기반) > **후행 연계**: STEP 8A 구현 전 완료 예정
- **1. proposal_artifacts** (산출물 버전 저장소) ```sql - id, proposal_id, node_name, output_key, version - created_at, created_by - is_active, is_deprecated - parent_node_name, parent_version - artifact_data (JSONB), artifact_size, checksum - used_by (JSONB), created_reason, notes ```
- - [ ] Diff view에서 버전 간 차이 표시 - [ ] Rollback 후 이전 상태 복원 - [ ] 자동 아카이빙 정책 동작
- **1. proposal_artifacts** (산출물 버전 저장소) ```sql - id, proposal_id, node_name, output_key, version - created_at, created_by - is_active, is_deprecated - parent_node_name, parent_version - artifact_data (JSONB), artifact_size, checksum - used_by (JSONB), created_reason, notes ```
- ```sql -- 001_artifact_versioning.sql CREATE TABLE proposal_artifacts ( id UUID PRIMARY KEY, proposal_id UUID NOT NULL REFERENCES proposals(id), node_name VARCHAR NOT NULL, output_key VARCHAR NOT NULL, version INT NOT NULL, created_at TIMESTAMP DEFAULT NOW(), created_by UUID NOT NULL, is_active…
