# 🔧 State 모델 설계 & python
Cohesion: 0.13 | Nodes: 22

## Key Nodes
- **🔧 State 모델 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 10 connections
  - -> contains -> [[state]]
  - -> has_code_example -> [[python]]
  - -> contains -> [[versionmanagerpy]]
  - -> contains -> [[versionselectionmodaltsx]]
  - -> contains -> [[phase-1-2]]
  - -> contains -> [[phase-2-2]]
  - -> contains -> [[phase-1]]
  - -> contains -> [[phase-2]]
  - <- contains <- [[artifactversion-system]]
  - <- contains <- [[state]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 7 connections
  - <- has_code_example <- [[1-api]]
  - <- has_code_example <- [[2-api]]
  - <- has_code_example <- [[3-api-1]]
  - <- has_code_example <- [[4-api-2]]
  - <- has_code_example <- [[5-api-phase-3]]
  - <- has_code_example <- [[state]]
  - <- has_code_example <- [[versionmanagerpy]]
- **🔌 API 엔드포인트 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 6 connections
  - -> contains -> [[1-api]]
  - -> contains -> [[2-api]]
  - -> contains -> [[3-api-1]]
  - -> contains -> [[4-api-2]]
  - -> contains -> [[5-api-phase-3]]
  - <- contains <- [[artifactversion-system]]
- **ARTIFACT_VERSION System 설계서** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 4 connections
  - -> contains -> [[3]]
  - -> contains -> [[db]]
  - -> contains -> [[api]]
  - -> contains -> [[state]]
- **📊 DB 스키마 상세 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 4 connections
  - -> contains -> [[1-proposalartifacts]]
  - -> contains -> [[2-proposalartifactchoices]]
  - -> contains -> [[sql]]
  - <- contains <- [[artifactversion-system]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 3 connections
  - <- has_code_example <- [[1-proposalartifacts]]
  - <- has_code_example <- [[2-proposalartifactchoices]]
  - <- has_code_example <- [[sql]]
- **1️⃣ 버전 조회 API** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **테이블 1: proposal_artifacts** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **2️⃣ 의존성 검증 API** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **테이블 2: proposal_artifact_choices** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **3️⃣ 노드 이동 API (1단계: 검증)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **4️⃣ 노드 이동 API (2단계: 실행)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **5️⃣ 버전 비교 API (Phase 3)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **마이그레이션 SQL** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **version_manager.py (신규 파일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[state]]
- **VersionSelectionModal.tsx** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[state]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 1 connections
  - <- has_code_example <- [[versionselectionmodaltsx]]
- **3가지 핵심 설계 결정** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 1 connections
  - <- contains <- [[artifactversion-system]]
- **Phase 1 검증** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 1 connections
  - <- contains <- [[state]]
- **Phase 1: 기본 버전화 (2일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 1 connections
  - <- contains <- [[state]]
- **Phase 2 검증** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 1 connections
  - <- contains <- [[state]]
- **Phase 2: 버전 선택 (2일)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\artifact-version-system.design.md) -- 1 connections
  - <- contains <- [[state]]

## Internal Relationships
- 1️⃣ 버전 조회 API -> has_code_example -> python [EXTRACTED]
- 테이블 1: proposal_artifacts -> has_code_example -> sql [EXTRACTED]
- 2️⃣ 의존성 검증 API -> has_code_example -> python [EXTRACTED]
- 테이블 2: proposal_artifact_choices -> has_code_example -> sql [EXTRACTED]
- 3️⃣ 노드 이동 API (1단계: 검증) -> has_code_example -> python [EXTRACTED]
- 4️⃣ 노드 이동 API (2단계: 실행) -> has_code_example -> python [EXTRACTED]
- 5️⃣ 버전 비교 API (Phase 3) -> has_code_example -> python [EXTRACTED]
- 🔌 API 엔드포인트 설계 -> contains -> 1️⃣ 버전 조회 API [EXTRACTED]
- 🔌 API 엔드포인트 설계 -> contains -> 2️⃣ 의존성 검증 API [EXTRACTED]
- 🔌 API 엔드포인트 설계 -> contains -> 3️⃣ 노드 이동 API (1단계: 검증) [EXTRACTED]
- 🔌 API 엔드포인트 설계 -> contains -> 4️⃣ 노드 이동 API (2단계: 실행) [EXTRACTED]
- 🔌 API 엔드포인트 설계 -> contains -> 5️⃣ 버전 비교 API (Phase 3) [EXTRACTED]
- ARTIFACT_VERSION System 설계서 -> contains -> 3가지 핵심 설계 결정 [EXTRACTED]
- ARTIFACT_VERSION System 설계서 -> contains -> 📊 DB 스키마 상세 설계 [EXTRACTED]
- ARTIFACT_VERSION System 설계서 -> contains -> 🔌 API 엔드포인트 설계 [EXTRACTED]
- ARTIFACT_VERSION System 설계서 -> contains -> 🔧 State 모델 설계 [EXTRACTED]
- 📊 DB 스키마 상세 설계 -> contains -> 테이블 1: proposal_artifacts [EXTRACTED]
- 📊 DB 스키마 상세 설계 -> contains -> 테이블 2: proposal_artifact_choices [EXTRACTED]
- 📊 DB 스키마 상세 설계 -> contains -> 마이그레이션 SQL [EXTRACTED]
- 마이그레이션 SQL -> has_code_example -> sql [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> 🔧 State 모델 설계 [EXTRACTED]
- 🔧 State 모델 설계 -> has_code_example -> python [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> version_manager.py (신규 파일) [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> VersionSelectionModal.tsx [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> Phase 1: 기본 버전화 (2일) [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> Phase 2: 버전 선택 (2일) [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> Phase 1 검증 [EXTRACTED]
- 🔧 State 모델 설계 -> contains -> Phase 2 검증 [EXTRACTED]
- version_manager.py (신규 파일) -> has_code_example -> python [EXTRACTED]
- VersionSelectionModal.tsx -> has_code_example -> typescript [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 🔧 State 모델 설계, python, 🔌 API 엔드포인트 설계를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 artifact-version-system.design.md이다.

### Key Facts
- ```python 요청 GET /proposals/{proposal_id}/artifact-versions?output_key=strategy
- > **작성일**: 2026-03-30 > **목표**: 산출물 버전 관리 + 의존성 해결의 상세 설계 > **설계 대상**: Phase 1 + Phase 2 (기본 버전화 + 버전 선택) > **다음 단계**: Do Phase (Phase 1 구현)
- 테이블 1: proposal_artifacts
- ```sql CREATE TABLE proposal_artifacts ( -- 기본 식별자 id UUID PRIMARY KEY DEFAULT gen_random_uuid(), proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
- **GET** `/proposals/{proposal_id}/artifact-versions`
