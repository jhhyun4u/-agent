# Design: hwp-output & 2. 컴포넌트 설계
Cohesion: 0.12 | Nodes: 20

## Key Nodes
- **Design: hwp-output** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6-v2]]
- **2. 컴포넌트 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 5 connections
  - -> contains -> [[2-1-appserviceshwpxbuilderpy]]
  - -> contains -> [[2-2-appservicesphaseexecutorpy-hwpx]]
  - -> contains -> [[2-3-appapiroutesv31py]]
  - -> contains -> [[2-4-frontendappproposalsidpagetsx]]
  - <- contains <- [[design-hwp-output]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 3 connections
  - <- has_code_example <- [[metadata]]
  - <- has_code_example <- [[phase-4]]
  - <- has_code_example <- [[hwpxmetadata-phaseexecutor]]
- **text** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 3 connections
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2-1-appserviceshwpxbuilderpy]]
  - <- has_code_example <- [[3]]
- **2-1. `app/services/hwpx_builder.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 3 connections
  - -> has_code_example -> [[text]]
  - -> contains -> [[metadata]]
  - <- contains <- [[2]]
- **2-2. `app/services/phase_executor.py` — HWPX 통합** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 3 connections
  - -> contains -> [[phase-4]]
  - -> contains -> [[hwpxmetadata-phaseexecutor]]
  - <- contains <- [[2]]
- **3. 데이터 흐름** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 3 connections
  - -> has_code_example -> [[sql]]
  - -> has_code_example -> [[text]]
  - <- contains <- [[design-hwp-output]]
- **1. 아키텍처 개요** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[text]]
  - <- contains <- [[design-hwp-output]]
- **2-3. `app/api/routes_v31.py` — 다운로드 엔드포인트** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[http]]
  - <- contains <- [[2]]
- **2-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[tsx]]
  - <- contains <- [[2]]
- **5. 의존성** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[toml]]
  - <- contains <- [[design-hwp-output]]
- **hwpx_metadata 구성 (phase_executor에서 자동 조립)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-2-appservicesphaseexecutorpy-hwpx]]
- **metadata 스펙** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-1-appserviceshwpxbuilderpy]]
- **Phase 4 완료 후 빌드 순서** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-2-appservicesphaseexecutorpy-hwpx]]
- **http** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 1 connections
  - <- has_code_example <- [[2-3-appapiroutesv31py]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 1 connections
  - <- has_code_example <- [[3]]
- **toml** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 1 connections
  - <- has_code_example <- [[5]]
- **tsx** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 1 connections
  - <- has_code_example <- [[2-4-frontendappproposalsidpagetsx]]
- **4. 오류 처리 전략** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 1 connections
  - <- contains <- [[design-hwp-output]]
- **6. 미결 사항 (v2 이관)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\hwp-output.design.md) -- 1 connections
  - <- contains <- [[design-hwp-output]]

## Internal Relationships
- 1. 아키텍처 개요 -> has_code_example -> text [EXTRACTED]
- 2. 컴포넌트 설계 -> contains -> 2-1. `app/services/hwpx_builder.py` [EXTRACTED]
- 2. 컴포넌트 설계 -> contains -> 2-2. `app/services/phase_executor.py` — HWPX 통합 [EXTRACTED]
- 2. 컴포넌트 설계 -> contains -> 2-3. `app/api/routes_v31.py` — 다운로드 엔드포인트 [EXTRACTED]
- 2. 컴포넌트 설계 -> contains -> 2-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼 [EXTRACTED]
- 2-1. `app/services/hwpx_builder.py` -> has_code_example -> text [EXTRACTED]
- 2-1. `app/services/hwpx_builder.py` -> contains -> metadata 스펙 [EXTRACTED]
- 2-2. `app/services/phase_executor.py` — HWPX 통합 -> contains -> Phase 4 완료 후 빌드 순서 [EXTRACTED]
- 2-2. `app/services/phase_executor.py` — HWPX 통합 -> contains -> hwpx_metadata 구성 (phase_executor에서 자동 조립) [EXTRACTED]
- 2-3. `app/api/routes_v31.py` — 다운로드 엔드포인트 -> has_code_example -> http [EXTRACTED]
- 2-4. `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼 -> has_code_example -> tsx [EXTRACTED]
- 3. 데이터 흐름 -> has_code_example -> sql [EXTRACTED]
- 3. 데이터 흐름 -> has_code_example -> text [EXTRACTED]
- 5. 의존성 -> has_code_example -> toml [EXTRACTED]
- Design: hwp-output -> contains -> 1. 아키텍처 개요 [EXTRACTED]
- Design: hwp-output -> contains -> 2. 컴포넌트 설계 [EXTRACTED]
- Design: hwp-output -> contains -> 3. 데이터 흐름 [EXTRACTED]
- Design: hwp-output -> contains -> 4. 오류 처리 전략 [EXTRACTED]
- Design: hwp-output -> contains -> 5. 의존성 [EXTRACTED]
- Design: hwp-output -> contains -> 6. 미결 사항 (v2 이관) [EXTRACTED]
- hwpx_metadata 구성 (phase_executor에서 자동 조립) -> has_code_example -> python [EXTRACTED]
- metadata 스펙 -> has_code_example -> python [EXTRACTED]
- Phase 4 완료 후 빌드 순서 -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: hwp-output, 2. 컴포넌트 설계, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 hwp-output.design.md이다.

### Key Facts
- 2-1. `app/services/hwpx_builder.py`
- | 항목 | 내용 | | ---- | ---- | | Feature | hwp-output | | 설계일 | 2026-03-07 | | 기준 Plan | docs/01-plan/features/hwp-output.plan.md | | 구현 상태 | 완료 (proposal-platform-v1 Act-2에서 통합) | | 기술 접근 | Option C — python-hwpx 라이브러리 (v2.5) |
- ```text RFP 파싱 └─ Phase 4 실행 (proposal_generator) └─ Phase4Artifact.sections (dict) ├─ docx_builder.build_docx()     → .docx ├─ pptx_builder.build_pptx()     → .pptx └─ hwpx_builder.build_hwpx()     → .hwpx └─ phase_executor._upload_to_storage() └─ Supabase Storage (proposal-files 버킷) └─…
- 기술 선택: python-hwpx (v2.5) — `HwpxDocument` API
- ```sql -- proposals 테이블 storage_path_docx       TEXT, storage_path_pptx       TEXT, storage_path_hwpx       TEXT,   -- 신규 컬럼 storage_upload_failed   BOOLEAN ```
